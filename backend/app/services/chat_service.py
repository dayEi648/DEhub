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
from app.prompts.chat_prompts import CONVERSATION_TITLE_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.user_memory_service import UserMemoryService

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

    负责对话消息持久化、LangGraph 工作流编排、标题生成和画像摘要触发。
    """

    # 每达到多少条消息就重新生成用户画像摘要
    _SUMMARY_INTERVAL = 6

    # 标题重生成阈值（秒）：距上次消息超过此时长则重新生成标题
    _TITLE_REGENERATE_THRESHOLD_SECONDS = 300

    # 生成标题的最大长度（字符）
    _TITLE_MAX_LENGTH = 20

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

    def __init__(self, db: Session):
        self.db = db
        self.graph = get_chat_graph()
        self.memory_service = UserMemoryService(db)
        self._background_tasks: set[asyncio.Task] = set()

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

        # 持久化用户消息
        await asyncio.to_thread(
            msg_crud.create_conversation_message,
            self.db,
            conversation_id,
            "user",
            chat_in.user_input,
        )

        config = {"configurable": {"thread_id": conversation_id}}

        # 获取调用前的 checkpoint 状态，用于计算本轮新增消息数量
        try:
            state_before = await self.graph.aget_state(config)
            history_len = len(state_before.values.get("messages", [])) if state_before else 0
        except Exception:
            logger.exception("获取 checkpoint 状态失败，假设为新对话")
            history_len = 0

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
                        "display": False,
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

        # 标题生成和画像摘要改为后台异步执行，不阻塞响应
        if not chat_in.is_edit:
            task = asyncio.create_task(
                self._run_in_new_session(
                    self._ensure_title_async, chat_in, conversation_id
                )
            )
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        task = asyncio.create_task(
            self._run_in_new_session(
                self._maybe_sync_summary_async, user_id, conversation_id
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
            should_regenerate = False
            should_regenerate = (
                chat_in.conversation_id is None
                or last_at is None
                or (now - last_at).total_seconds() > self._TITLE_REGENERATE_THRESHOLD_SECONDS
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

    async def _maybe_sync_summary_async(
        self, user_id: int, conversation_id: int
    ) -> None:
        """
        检查当前对话消息数，若达到阈值则触发用户画像摘要生成。
        """
        try:
            conv = await asyncio.to_thread(
                conv_crud.get_ai_conversation_by_id, self.db, conversation_id
            )
            if conv is None:
                return

            current_count = await asyncio.to_thread(
                msg_crud.count_conversation_messages,
                self.db,
                conversation_id,
            )
            last_count = conv.summary_message_count or 0

            if current_count >= self._SUMMARY_INTERVAL and (
                current_count - last_count
            ) >= self._SUMMARY_INTERVAL:
                await self.memory_service.sync_conversation_summary_async(
                    user_id, conversation_id
                )
                await asyncio.to_thread(
                    conv_crud.update_summary_message_count,
                    self.db,
                    conversation_id,
                    current_count,
                )
        except Exception:
            logger.exception("判断画像摘要触发失败: conv=%s", conversation_id)

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
    ) -> list:
        """
        获取对话消息列表。

        默认过滤掉 meta 中标记为 display=False 的中间消息（如 tool_calls 决策消息），
        仅当 include_hidden=True 时返回完整消息流（供管理监控使用）。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
            skip: 跳过数量
            limit: 限制数量
            include_hidden: 是否包含隐藏的中间消息
        Returns:
            list[ConversationMessage]
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
            messages = [
                m for m in messages
                if not (m.meta and m.meta.get("display") is False)
            ]

        return messages

    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """
        物理删除对话，并清理 Checkpointer。
        向量库中的画像摘要会被保留，作为长期记忆供后续检索使用。

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
