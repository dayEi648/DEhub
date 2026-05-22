import asyncio
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from sqlalchemy.orm import Session

from app.crud import ai_conversation as conv_crud
from app.crud import conversation_message as msg_crud
from app.db.session import SessionLocal
from app.graphs.builders.chat_builder import get_chat_graph
from app.infrastructure.checkpoint_client import delete_checkpoint
from app.infrastructure.llm_client import get_llm_small_client
from app.models.ai_conversation import AIConversation
from app.prompts.chat_prompts import CHAT_DEFAULT_SYSTEM_PROMPT, CONVERSATION_TITLE_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse, MessageResponse
from app.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)


def _require_owner(conv: AIConversation, user_id: int) -> None:
    """校验当前用户是否为对话所有者。"""
    if conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该对话",
        )


class ChatService:
    """AI 对话服务。

    负责对话消息持久化、LangGraph 工作流编排、标题生成和用户画像更新触发。
    """

    # 标题重生成阈值（秒）：距上次消息超过此时长则重新生成标题
    _TITLE_REGENERATE_THRESHOLD_SECONDS = 300

    # 生成标题的最大长度（字符）
    _TITLE_MAX_LENGTH = 20

    # 用户画像更新触发间隔：每 N 条用户消息触发一次判断
    _PROFILE_UPDATE_INTERVAL = 3

    @staticmethod
    def _extract_ai_content(msg: AIMessage) -> str:
        """从 AIMessage 中提取可展示的文本内容。"""
        if isinstance(msg.content, str):
            content = msg.content or ""
        else:
            content = ""
        if not content:
            content = msg.additional_kwargs.get("reasoning_content", "") or ""
        return content

    @staticmethod
    def _has_displayable_content(message) -> bool:
        """判断消息是否包含可直接展示给用户的正文。"""
        content = getattr(message, "content", "") or ""
        return bool(content.strip())

    @classmethod
    def _is_visible_message(cls, message) -> bool:
        """默认消息列表中仅展示用户消息和有正文的 AI 回复。"""
        if message.role == "user":
            return True
        if message.role == "assistant":
            return cls._has_displayable_content(message)
        return False

    @staticmethod
    def _to_message_response(message, include_hidden: bool) -> MessageResponse:
        """转换为 API 响应对象，默认视图不暴露内部工具调用元数据。"""
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            meta=message.meta if include_hidden else None,
            created_at=message.created_at,
        )

    def __init__(self, db: Session):
        self.db = db
        self.graph = get_chat_graph()
        self.profile_service = UserProfileService(db)
        self._background_tasks: set[asyncio.Task] = set()

    @staticmethod
    def _db_messages_to_lc_messages(db_messages: list) -> list:
        """将数据库消息记录转换为 LangChain Message 对象列表。"""
        messages = []
        for msg in db_messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                kwargs: dict = {}
                if msg.meta and msg.meta.get("tool_calls"):
                    kwargs["tool_calls"] = [
                        {
                            "id": tc.get("id"),
                            "name": tc.get("name"),
                            "args": tc.get("args"),
                            "type": "tool_call",
                        }
                        for tc in msg.meta["tool_calls"]
                    ]
                messages.append(AIMessage(content=msg.content, **kwargs))
            elif msg.role == "system":
                messages.append(SystemMessage(content=msg.content))
            elif msg.role == "tool":
                kwargs: dict = {}
                if msg.meta:
                    if msg.meta.get("tool_call_id"):
                        kwargs["tool_call_id"] = msg.meta["tool_call_id"]
                    if msg.meta.get("name"):
                        kwargs["name"] = msg.meta["name"]
                messages.append(ToolMessage(content=msg.content, **kwargs))
        return messages

    def _build_system_message(self, user_id: int) -> SystemMessage:
        """构建包含固定指令和用户画像的 SystemMessage。"""
        profile_text = self.profile_service.get_profile_text(user_id)
        content = CHAT_DEFAULT_SYSTEM_PROMPT
        if profile_text:
            content += f"\n\n--- 用户画像 ---\n{profile_text}\n---"
        return SystemMessage(content=content)

    async def _restore_state_from_db(
        self, config: dict, conversation_id: int, user_id: int
    ) -> None:
        """从数据库加载对话历史，恢复到 Redis checkpoint 中（包含 SystemMessage）。"""
        db_messages = await asyncio.to_thread(
            msg_crud.list_conversation_messages,
            self.db,
            conversation_id,
            limit=None,
        )

        system_msg = self._build_system_message(user_id)
        if db_messages:
            history = self._db_messages_to_lc_messages(db_messages)
            messages = [system_msg] + history
        else:
            messages = [system_msg]

        await self.graph.aupdate_state(config, {"messages": messages})
        logger.info(
            "从数据库恢复对话历史到 checkpoint: conv=%s, messages=%d",
            conversation_id,
            len(messages),
        )

    async def chat(self, chat_in: ChatRequest, user_id: int) -> ChatResponse:
        """
        对话服务。

        Args:
            chat_in: ChatRequest
            user_id: 当前用户ID

        Returns:
            ChatResponse: 对话结果
        """
        # 无 conversation_id 时自动创建新对话
        if chat_in.conversation_id is None:
            conv = await asyncio.to_thread(
                conv_crud.create_ai_conversation,
                self.db,
                user_id=user_id,
                title="New Chat",
            )
            conversation_id = conv.id
        else:
            conv = await asyncio.to_thread(
                self.get_conversation_if_owned,
                chat_in.conversation_id,
                user_id,
            )
            conversation_id = chat_in.conversation_id

        config = {"configurable": {"thread_id": conversation_id}}

        # 获取调用前的 checkpoint 状态
        try:
            state_before = await self.graph.aget_state(config)
        except Exception:
            logger.exception("获取 checkpoint 状态失败，假设为新对话")
            state_before = None

        # 如果 checkpoint 存在但格式旧（无 SystemMessage），清理后重新初始化
        if state_before is not None:
            messages = state_before.values.get("messages", [])
            if not messages:
                state_before = None
            elif not isinstance(messages[0], SystemMessage):
                logger.info("检测到旧格式 checkpoint，清理后重新初始化")
                await delete_checkpoint(str(conversation_id))
                state_before = None

        # checkpoint 为 None 时：新对话、已过期、或刚清理的旧格式
        if state_before is None:
            if chat_in.conversation_id is not None:
                # 已有对话：从数据库恢复历史并注入 SystemMessage
                try:
                    await self._restore_state_from_db(config, conversation_id, user_id)
                    state_before = await self.graph.aget_state(config)
                except Exception:
                    logger.exception("从数据库恢复 checkpoint 失败，继续作为新对话")
                    state_before = None
            else:
                # 新对话：仅注入 SystemMessage
                try:
                    system_msg = self._build_system_message(user_id)
                    await self.graph.aupdate_state(
                        config, {"messages": [system_msg]}
                    )
                    state_before = await self.graph.aget_state(config)
                except Exception:
                    logger.exception("注入 SystemMessage 失败")
                    state_before = None

        history_len = (
            len(state_before.values.get("messages", [])) if state_before else 0
        )

        # 统计当前 checkpoint 中的 HumanMessage 数量（用于判断画像更新）
        current_messages = (
            state_before.values.get("messages", []) if state_before else []
        )
        human_count_before = sum(
            1 for m in current_messages if isinstance(m, HumanMessage)
        )

        # 持久化用户消息
        await asyncio.to_thread(
            msg_crud.create_conversation_message,
            self.db,
            conversation_id,
            "user",
            chat_in.user_input,
        )

        try:
            result = await self.graph.ainvoke(
                {
                    "messages": [HumanMessage(content=chat_in.user_input)],
                    "user_id": user_id,
                },
                config=config,
            )
        except Exception:
            logger.exception("Graph 调用失败，保留用户消息")
            raise

        # 兜底检查：确保 Graph 正常结束于 AIMessage
        final_msg = result["messages"][-1]
        if not isinstance(final_msg, AIMessage):
            logger.error(
                "Graph 返回的最后一条消息不是 AIMessage: type=%s", type(final_msg)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI 回复生成异常",
            )

        # 遍历本轮严格新增的消息，分类持久化
        for msg in result["messages"][history_len:]:
            if isinstance(msg, HumanMessage):
                # 用户输入已在调用 Graph 之前持久化，跳过
                continue

            if isinstance(msg, AIMessage):
                content = self._extract_ai_content(msg)
                metadata = None
                if msg.tool_calls:
                    metadata = {
                        "tool_calls": [
                            {
                                "id": tc.get("id"),
                                "name": tc.get("name"),
                                "args": tc.get("args"),
                            }
                            for tc in msg.tool_calls
                        ],
                        "display": bool(content.strip()),
                    }
                await asyncio.to_thread(
                    msg_crud.create_conversation_message,
                    self.db,
                    conversation_id,
                    "assistant",
                    content,
                    metadata=metadata,
                )

            elif isinstance(msg, ToolMessage):
                await asyncio.to_thread(
                    msg_crud.create_conversation_message,
                    self.db,
                    conversation_id,
                    "tool",
                    msg.content or "",
                    metadata={
                        "tool_call_id": msg.tool_call_id,
                        "name": msg.name,
                        "display": False,
                    },
                )

        # 标题生成（后台异步执行，不阻塞响应）
        if not chat_in.is_edit:
            task = asyncio.create_task(
                self._run_in_new_session(
                    self._ensure_title_async, chat_in, conversation_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        # 用户画像更新判断：每 N 条用户消息触发一次（编辑消息时不触发）
        if not chat_in.is_edit:
            human_count_after = human_count_before + 1
            if (
                human_count_after > 0
                and human_count_after % self._PROFILE_UPDATE_INTERVAL == 0
            ):
                task = asyncio.create_task(
                    self._run_in_new_session(
                        self._maybe_update_profile_async, user_id, conversation_id
                    )
                )
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

        # 提取最终回复文本用于接口返回
        final_content = self._extract_ai_content(final_msg)

        return ChatResponse(
            response=final_content,
            conversation_id=conversation_id,
        )

    @staticmethod
    async def _run_in_new_session(method, *args) -> None:
        """在新 Session 中异步运行指定方法，用于后台任务隔离。"""
        try:
            with SessionLocal() as db:
                service = ChatService(db)
                bound = getattr(service, method.__name__)
                await bound(*args)
        except Exception:
            logger.exception("后台任务 %s 失败", method.__name__)

    async def _maybe_update_profile_async(
        self, user_id: int, conversation_id: int
    ) -> None:
        """触发用户画像更新判断（后台任务）。"""
        try:
            await self.profile_service.maybe_update_user_profile(
                user_id, conversation_id
            )
        except Exception:
            logger.exception(
                "用户画像更新失败: user=%s conv=%s", user_id, conversation_id
            )

    async def _ensure_title_async(
        self, chat_in: ChatRequest, conversation_id: int
    ) -> None:
        """
        智能生成或更新对话标题。

        - 新对话首次消息：立即生成标题
        - 已有对话：距上次消息超过 5 分钟则重新生成，否则只更新 last_message_at
        """
        try:
            conv = await asyncio.to_thread(
                conv_crud.get_ai_conversation_by_id, self.db, conversation_id
            )
            if conv is None:
                return

            now = datetime.now(timezone.utc)
            last_at = conv.last_message_at

            # 兼容 naive datetime
            if last_at is not None and last_at.tzinfo is None:
                last_at = last_at.replace(tzinfo=timezone.utc)

            # 判断是否需要重新生成标题
            should_regenerate = (
                chat_in.conversation_id is None
                or last_at is None
                or (now - last_at).total_seconds()
                > self._TITLE_REGENERATE_THRESHOLD_SECONDS
            )

            if should_regenerate:
                title = await self._generate_title_async(chat_in.user_input)
                if title:
                    await asyncio.to_thread(
                        conv_crud.update_conversation_title,
                        self.db,
                        conversation_id,
                        title,
                    )

            await asyncio.to_thread(
                conv_crud.update_last_message_at, self.db, conversation_id
            )
        except Exception:
            logger.exception("标题生成失败: conv=%s", conversation_id)

    async def _generate_title_async(self, user_input: str) -> str:
        """调用 small LLM 生成对话标题，返回空字符串表示生成失败。"""
        try:
            response = await get_llm_small_client().ainvoke([
                SystemMessage(content=CONVERSATION_TITLE_PROMPT),
                HumanMessage(content=user_input),
            ])
            title = (
                response.content.strip().replace('"', "").replace("'", "")
                if isinstance(response.content, str)
                else ""
            )
            return title[:self._TITLE_MAX_LENGTH] if title else ""
        except Exception:
            return ""

    def get_conversation_if_owned(
        self, conversation_id: int, user_id: int
    ) -> AIConversation:
        """
        获取对话并校验权限。

        - 对话不存在或已删除 → 抛 404
        - 对话存在但不属于当前用户 → 抛 403

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID

        Returns:
            AIConversation
        """
        conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
        _require_owner(conv, user_id)
        return conv

    async def list_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list[AIConversation], int]:
        """
        获取当前用户的对话列表（按最近时间倒序）。
        Args:
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
        Returns:
            tuple[list[AIConversation], int]
        """
        return await asyncio.to_thread(
            conv_crud.list_ai_conversations_by_user,
            self.db,
            user_id,
            skip,
            limit,
        )

    async def get_messages(
        self,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        include_hidden: bool = False,
    ) -> list[MessageResponse]:
        """
        获取对话消息列表。

        默认只返回 user 和有正文的 assistant 消息，避免隐藏工具细节泄露给普通用户。
        仅当 include_hidden=True 时返回完整消息流与元数据（供管理监控使用）。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
            include_hidden: 是否包含隐藏的中间消息
        Returns:
            list[MessageResponse]
        """
        await asyncio.to_thread(
            self.get_conversation_if_owned, conversation_id, user_id
        )

        messages = await asyncio.to_thread(
            msg_crud.list_conversation_messages,
            self.db,
            conversation_id,
            skip,
            limit,
        )

        if not include_hidden:
            messages = [m for m in messages if self._is_visible_message(m)]

        return [
            self._to_message_response(m, include_hidden=include_hidden)
            for m in messages
        ]

    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """
        物理删除对话，并清理 Checkpointer。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
        """
        conv = await asyncio.to_thread(
            conv_crud.get_ai_conversation_by_id, self.db, conversation_id
        )
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
        _require_owner(conv, user_id)

        # 清理 Redis checkpoint，再物理删除 DB 记录（级联删除 messages）
        await delete_checkpoint(str(conversation_id))
        await asyncio.to_thread(
            conv_crud.delete_ai_conversation, self.db, conversation_id
        )
