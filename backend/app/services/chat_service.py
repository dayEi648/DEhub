import asyncio
import logging
import secrets
import unicodedata
from datetime import datetime, timezone

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.modifier import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from sqlalchemy.orm import Session

from app.crud import ai_conversation as conv_crud
from app.crud import conversation_message as msg_crud
from app.db.session import SessionLocal
from app.graphs.builders.chat_builder import get_chat_graph
from app.infrastructure.checkpoint_client import delete_checkpoint
from app.infrastructure.background_tasks import background_task_manager
from app.infrastructure.llm_client import get_llm_client, get_llm_small_client
from app.models.ai_conversation import AIConversation
from app.models.conversation_message import ConversationMessage
from app.prompts.chat_prompts import (
    CONVERSATION_TITLE_PROMPT,
    render_context_compact_prompt,
    render_chat_system_prompt,
    render_current_goal_prompt,
)
from app.redis_client import get_sync_redis_client
from app.core.config import settings
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

    # 从配置读取阈值，统一环境可调性
    _TITLE_REGENERATE_THRESHOLD_SECONDS = settings.AI_CHAT_TITLE_REGENERATE_THRESHOLD_SECONDS
    _TITLE_MAX_LENGTH = settings.AI_CHAT_TITLE_MAX_LENGTH
    _PROFILE_UPDATE_INTERVAL = settings.AI_CHAT_PROFILE_UPDATE_INTERVAL
    _MAIN_CONTEXT_WINDOW_TOKENS = settings.AI_CHAT_CONTEXT_WINDOW_TOKENS
    _COMPACT_THRESHOLD_RATIO = settings.AI_CHAT_COMPACT_THRESHOLD_RATIO
    _COMPACT_SUMMARY_MAX_CHARS = settings.AI_CHAT_COMPACT_SUMMARY_MAX_CHARS
    _COMPACT_PLACEHOLDER = "已自动压缩上下文"
    _COMPACT_LOCK_TTL_SECONDS = settings.AI_CHAT_COMPACT_LOCK_TTL_SECONDS
    _GOAL_TRANSCRIPT_LINES_LIMIT = settings.AI_CHAT_GOAL_TRANSCRIPT_LINES_LIMIT
    _GOAL_GENERATION_CHAR_THRESHOLD = settings.AI_CHAT_GOAL_GENERATION_CHAR_THRESHOLD

    @staticmethod
    def _extract_ai_content(msg: AIMessage) -> str:
        """从 AIMessage 中提取可展示的文本内容，兼容字符串与列表型 content。"""
        content = msg.content
        if isinstance(content, str):
            text = content or ""
        elif isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    parts.append(str(part.get("text") or part.get("content") or ""))
                else:
                    parts.append(str(part))
            text = "".join(parts)
        else:
            text = str(content) if content is not None else ""
        if not text:
            text = msg.additional_kwargs.get("reasoning_content", "") or ""
        return text

    @staticmethod
    def _has_displayable_content(message) -> bool:
        """判断消息是否包含可直接展示给用户的正文。"""
        content = getattr(message, "content", "") or ""
        return bool(content.strip())

    @classmethod
    def _is_visible_message(cls, message) -> bool:
        """默认消息列表中仅展示用户消息和有正文的 AI 回复；含 tool_calls 的对普通用户隐藏。"""
        if cls._is_compact_summary_db_message(message):
            return True
        if message.role == "user":
            return True
        if message.role == "assistant":
            if not cls._has_displayable_content(message):
                return False
            # 包含 tool_calls 的 AIMessage 视为中间决策消息，对普通用户隐藏
            if message.meta and message.meta.get("tool_calls"):
                return False
            return True
        return False

    @staticmethod
    def _to_message_response(message, include_hidden: bool) -> MessageResponse:
        """转换为 API 响应对象，默认视图不暴露内部工具调用元数据。"""
        if ChatService._is_compact_summary_db_message(message):
            return MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=ChatService._COMPACT_PLACEHOLDER,
                meta={"compact_summary": True},
                created_at=message.created_at,
            )
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            meta=message.meta if include_hidden else None,
            created_at=message.created_at,
        )

    def __init__(self, db: Session, permission_level: int = 0):
        self.db = db
        self.permission_level = permission_level
        self.graph = get_chat_graph(permission_level=permission_level)
        self.profile_service = UserProfileService(db)
        self._background_tasks = background_task_manager

    @classmethod
    def _chat_lock_key(cls, conversation_id: int) -> str:
        return f"dehub:ai_chat:lock:{conversation_id}"

    @classmethod
    async def _acquire_conversation_lock(cls, conversation_id: int) -> str:
        """获取对话级锁；Redis 不可用时返回 503，不再降级无锁执行。"""
        def _acquire() -> str:
            redis = get_sync_redis_client()
            token = secrets.token_urlsafe(12)
            acquired = redis.set(
                cls._chat_lock_key(conversation_id),
                token,
                nx=True,
                ex=cls._COMPACT_LOCK_TTL_SECONDS,
            )
            return token if acquired is True else ""

        try:
            token = await asyncio.to_thread(_acquire)
        except Exception:
            logger.exception("获取 AI 对话锁失败: conv=%s", conversation_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="对话锁服务暂不可用，请稍后再试",
            ) from None

        if token == "":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="当前对话正在生成或压缩上下文，请稍后再试",
            )
        return token

    @classmethod
    async def _release_conversation_lock(
        cls, conversation_id: int, token: str | None
    ) -> None:
        """释放对话级锁，仅释放自己持有的 token。"""
        if not token:
            return

        def _release() -> None:
            redis = get_sync_redis_client()
            key = cls._chat_lock_key(conversation_id)
            current = redis.get(key)
            if isinstance(current, bytes):
                current = current.decode("utf-8")
            if current == token:
                redis.delete(key)

        try:
            await asyncio.to_thread(_release)
        except Exception:
            logger.warning("释放 AI 对话锁失败: conv=%s", conversation_id, exc_info=True)

    @staticmethod
    def _is_compact_summary_db_message(message) -> bool:
        """判断数据库消息是否为 compact summary。"""
        meta = getattr(message, "meta", None) or {}
        return bool(meta.get("compact_summary"))

    @staticmethod
    def _is_compact_summary_lc_message(message) -> bool:
        """判断 LangChain 消息是否为 compact summary。"""
        return isinstance(message, AIMessage) and bool(
            message.additional_kwargs.get("compact_summary")
        )

    @staticmethod
    def _db_messages_to_lc_messages(db_messages: list) -> list:
        """将数据库消息记录转换为 LangChain Message 对象列表。"""
        messages = []
        for msg in db_messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                ai_kwargs: dict = {}
                if msg.meta and msg.meta.get("tool_calls"):
                    ai_kwargs["tool_calls"] = [
                        {
                            "id": tc.get("id"),
                            "name": tc.get("name"),
                            "args": tc.get("args"),
                            "type": "tool_call",
                        }
                        for tc in msg.meta["tool_calls"]
                    ]
                if msg.meta and msg.meta.get("compact_summary"):
                    ai_kwargs["additional_kwargs"] = {"compact_summary": True}
                messages.append(AIMessage(content=msg.content, **ai_kwargs))
            elif msg.role == "system":
                messages.append(SystemMessage(content=msg.content))
            elif msg.role == "tool":
                tool_kwargs: dict = {}
                if msg.meta:
                    if msg.meta.get("tool_call_id"):
                        tool_kwargs["tool_call_id"] = msg.meta["tool_call_id"]
                    if msg.meta.get("name"):
                        tool_kwargs["name"] = msg.meta["name"]
                messages.append(ToolMessage(content=msg.content, **tool_kwargs))
        return messages

    @staticmethod
    def _serialize_lc_message(message) -> dict:
        """序列化少量需要随 compact summary 保留的消息。"""
        if isinstance(message, HumanMessage):
            return {"role": "user", "content": message.content or ""}
        if isinstance(message, AIMessage):
            return {"role": "assistant", "content": ChatService._extract_ai_content(message)}
        if isinstance(message, ToolMessage):
            return {
                "role": "tool",
                "content": message.content or "",
                "tool_call_id": message.tool_call_id,
                "name": message.name,
            }
        return {"role": "unknown", "content": getattr(message, "content", "") or ""}

    @staticmethod
    def _deserialize_retained_messages(raw_messages: list | None) -> list:
        """反序列化 compact summary 元数据中保留的最近一轮消息。"""
        if not raw_messages:
            return []
        messages = []
        for raw in raw_messages:
            if not isinstance(raw, dict):
                continue
            role = raw.get("role")
            content = raw.get("content") or ""
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "tool":
                tool_call_id = raw.get("tool_call_id") or "compact_tool_call"
                messages.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                        name=raw.get("name"),
                    )
                )
        return messages

    @staticmethod
    def _snapshot_checkpoint_state(state) -> dict:
        """复制 Graph 调用前的 checkpoint 关键状态，供失败回滚使用。"""
        values = getattr(state, "values", None) or {}
        snapshot = {"messages": list(values.get("messages") or [])}
        for key in ("profile_text", "current_goal"):
            if values.get(key) is not None:
                snapshot[key] = values.get(key)
        return snapshot

    async def _rollback_checkpoint_state(self, config: dict, snapshot: dict) -> None:
        """将 checkpoint 恢复到 Graph 调用前，避免失败轮次污染上下文。"""
        payload = {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *snapshot.get("messages", []),
            ]
        }
        for key in ("profile_text", "current_goal"):
            if key in snapshot:
                payload[key] = snapshot[key]
        await self.graph.aupdate_state(config, payload)

    @classmethod
    def _build_checkpoint_history_from_db(cls, db_messages: list) -> list:
        """从数据库恢复 checkpoint 历史，优先使用最新 compact summary 折叠旧历史。"""
        latest_summary_index = None
        for index, msg in enumerate(db_messages):
            if cls._is_compact_summary_db_message(msg):
                latest_summary_index = index

        if latest_summary_index is None:
            return cls._db_messages_to_lc_messages(db_messages)

        summary_msg = db_messages[latest_summary_index]
        summary_messages = cls._db_messages_to_lc_messages([summary_msg])
        retained = cls._deserialize_retained_messages(
            (summary_msg.meta or {}).get("retained_messages")
        )
        after_summary = cls._db_messages_to_lc_messages(
            db_messages[latest_summary_index + 1:]
        )
        return [*summary_messages, *retained, *after_summary]

    async def _restore_state_from_db(
        self, config: dict, conversation_id: int, user_id: int
    ) -> None:
        """从数据库加载对话历史，恢复到 Redis checkpoint 中（不注入 SystemMessage）。"""
        db_messages = await asyncio.to_thread(
            msg_crud.list_conversation_messages,
            self.db,
            conversation_id,
            limit=None,
        )

        history = self._build_checkpoint_history_from_db(db_messages) if db_messages else []
        state_update: dict = {"messages": history}

        # 恢复时加载一次用户画像并写入 checkpoint（后续轮次直接复用 state 中的值）
        profile_text = self.profile_service.get_profile_text(user_id)
        if profile_text:
            state_update["profile_text"] = profile_text

        await self.graph.aupdate_state(config, state_update)
        logger.info(
            "从数据库恢复对话历史到 checkpoint: conv=%s, messages=%d",
            conversation_id,
            len(history),
        )

    @staticmethod
    def _extract_current_turn_messages(result_messages: list) -> list:
        """从结果消息列表中提取当前轮次新增的消息。

        history_len 不可靠时从最后一个 HumanMessage 后截取，
        找不到则兜底保留最终 AIMessage。
        """
        for i in range(len(result_messages) - 1, -1, -1):
            if isinstance(result_messages[i], HumanMessage):
                return result_messages[i + 1:]
        # 未找到 HumanMessage 边界，至少保留最终 AIMessage
        for i in range(len(result_messages) - 1, -1, -1):
            if isinstance(result_messages[i], AIMessage):
                return [result_messages[i]]
        return []

    @staticmethod
    def _safe_truncate(text: str, max_len: int) -> str:
        """安全截断文本，回退到最后一个非组合字符边界，避免切断组合字符。"""
        if len(text) <= max_len:
            return text
        pos = max_len
        while pos > 0 and unicodedata.category(text[pos]) == "Mn":
            pos -= 1
        return text[:pos] if pos > 0 else text[:max_len]

    @classmethod
    def _compact_aware_messages(cls, messages: list) -> list:
        """返回最新 compact summary 及其后的消息；未压缩则返回原消息。"""
        latest_summary_index = None
        for index, msg in enumerate(messages):
            if cls._is_compact_summary_lc_message(msg):
                latest_summary_index = index
        if latest_summary_index is None:
            return messages
        return messages[latest_summary_index:]

    @classmethod
    def _message_to_transcript_line(cls, message) -> str | None:
        """将 LangChain 消息转换为 small model 可读的 transcript 行。"""
        if isinstance(message, SystemMessage):
            return None
        if isinstance(message, HumanMessage):
            return f"user: {message.content}"
        if isinstance(message, AIMessage):
            if message.tool_calls:
                return None
            prefix = "compact_summary" if cls._is_compact_summary_lc_message(message) else "assistant"
            return f"{prefix}: {cls._extract_ai_content(message)}"
        if isinstance(message, ToolMessage):
            return f"tool: {message.content or ''}"
        return None

    @classmethod
    def _messages_to_transcript(cls, messages: list) -> str:
        """将消息列表整理为 transcript，自动隐藏内部 system/tool_call 噪声。"""
        lines = []
        for message in messages:
            line = cls._message_to_transcript_line(message)
            if line:
                lines.append(line)
        return "\n".join(lines)

    @classmethod
    def _count_goal_context_chars(cls, messages: list) -> int:
        """计算 goal 生成上下文长度，compact summary 也计入。"""
        return sum(
            len(line)
            for line in (
                cls._message_to_transcript_line(m) or ""
                for m in cls._compact_aware_messages(messages)
            )
        )

    @classmethod
    def _build_compact_payload(cls, messages: list) -> tuple[str, list]:
        """构造 compact 输入 transcript，并返回需要保留的最新一轮消息。"""
        latest_human_index = None
        for index in range(len(messages) - 1, -1, -1):
            if isinstance(messages[index], HumanMessage):
                latest_human_index = index
                break

        retained_messages: list = []
        compact_candidates = messages
        if latest_human_index is not None:
            retained_messages = [messages[latest_human_index]]
            for message in reversed(messages[latest_human_index + 1:]):
                if isinstance(message, AIMessage) and not message.tool_calls:
                    retained_messages.append(message)
                    break
            compact_candidates = messages[:latest_human_index]

        transcript = cls._messages_to_transcript(compact_candidates)
        return transcript, retained_messages

    async def _generate_current_goal(
        self,
        conversation_id: int,
        user_input: str,
        previous_goal: str | None,
        current_messages: list,
    ) -> str | None:
        """根据对话上下文调用 small model 生成 current_goal，返回 5~200 字描述或 None。"""
        # compact 后只使用最新摘要及摘要后的新消息；未 compact 时限制最近消息数量。
        context_messages = self._compact_aware_messages(current_messages)
        transcript_lines = [
            line for line in (
                self._message_to_transcript_line(m) for m in context_messages
            ) if line
        ]
        if not any(self._is_compact_summary_lc_message(m) for m in context_messages):
            transcript_lines = transcript_lines[-self._GOAL_TRANSCRIPT_LINES_LIMIT:]
        transcript_lines.append(f"user: {user_input}")
        conversation = "\n".join(transcript_lines)

        prompt = render_current_goal_prompt(
            conversation=conversation,
            previous_goal=previous_goal,
        )

        try:
            response = await get_llm_small_client().ainvoke([
                SystemMessage(content=prompt),
            ])
            goal = response.content.strip() if isinstance(response.content, str) else ""
            if len(goal) < 5:
                return None
            if len(goal) > 200:
                goal = ChatService._safe_truncate(goal, 197) + "..."
            return goal
        except Exception:
            logger.exception("生成 current_goal 失败，保留旧值")
            return previous_goal

    async def chat(self, chat_in: ChatRequest, user_id: int) -> ChatResponse:
        """对话服务主入口。"""
        # 无 conversation_id 时自动创建新对话
        created_new_conversation = chat_in.conversation_id is None
        if created_new_conversation:
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
        try:
            lock_token = await self._acquire_conversation_lock(conversation_id)
        except Exception:
            if created_new_conversation:
                try:
                    await asyncio.to_thread(
                        conv_crud.delete_ai_conversation,
                        self.db,
                        conversation_id,
                    )
                except Exception:
                    logger.exception(
                        "新对话获取锁失败后清理空对话失败: conv=%s",
                        conversation_id,
                    )
            raise

        try:
            # 获取调用前的 checkpoint 状态
            try:
                state_before = await self.graph.aget_state(config)
            except Exception:
                logger.exception("获取 checkpoint 状态失败，假设为新对话")
                state_before = None

            # 弱化旧格式检测：仅当 checkpoint 结构明显异常（消息列表无法解析）时清理
            if state_before is not None:
                messages = state_before.values.get("messages", [])
                if not messages:
                    state_before = None
                # 不再因首条是 SystemMessage 或非 SystemMessage 而删除 checkpoint
                # 旧 SystemMessage 由 PromptAssemblyMiddleware 在请求前过滤

            # checkpoint 为 None 时：新对话、已过期、或消息为空
            if state_before is None:
                if chat_in.conversation_id is not None:
                    # 已有对话：从数据库恢复历史
                    try:
                        await self._restore_state_from_db(config, conversation_id, user_id)
                        state_before = await self.graph.aget_state(config)
                    except Exception:
                        logger.exception("从数据库恢复 checkpoint 失败，继续作为新对话")
                        state_before = None
                else:
                    # 新对话：初始化 profile_text
                    try:
                        profile_text = self.profile_service.get_profile_text(user_id)
                        state_update: dict = {"messages": []}
                        if profile_text:
                            state_update["profile_text"] = profile_text
                        await self.graph.aupdate_state(config, state_update)
                        state_before = await self.graph.aget_state(config)
                    except Exception:
                        logger.exception("初始化新对话 checkpoint 失败")
                        state_before = None

            history_len = (
                len(state_before.values.get("messages", [])) if state_before else 0
            )

            current_messages = (
                state_before.values.get("messages", []) if state_before else []
            )

            # 从 state 读取或补加载 profile_text
            profile_text = state_before.values.get("profile_text") if state_before else None
            if not profile_text:
                profile_text = self.profile_service.get_profile_text(user_id)
                if state_before and profile_text:
                    try:
                        await self.graph.aupdate_state(
                            config, {"profile_text": profile_text}
                        )
                    except Exception:
                        logger.exception("补写入 profile_text 失败")

            # 计算 compact-aware 上下文字数，决定是否生成 current_goal
            user_chars_total = self._count_goal_context_chars(current_messages) + len(
                chat_in.user_input
            )
            previous_goal = state_before.values.get("current_goal") if state_before else None
            if user_chars_total < self._GOAL_GENERATION_CHAR_THRESHOLD:
                current_goal = previous_goal
            else:
                current_goal = await self._generate_current_goal(
                    conversation_id=conversation_id,
                    user_input=chat_in.user_input,
                    previous_goal=previous_goal,
                    current_messages=current_messages,
                )

            # 确定当前场景
            prompt_scene = "对话开始" if chat_in.conversation_id is None else "持续对话"
            checkpoint_snapshot = self._snapshot_checkpoint_state(state_before)

            # 持久化用户消息（Graph 异常时将回滚，避免孤立 user 消息）
            user_msg = await asyncio.to_thread(
                msg_crud.create_conversation_message,
                self.db,
                conversation_id,
                "user",
                chat_in.user_input,
            )
            user_message_count = await asyncio.to_thread(
                msg_crud.count_conversation_messages_by_role,
                self.db,
                conversation_id,
                "user",
            )
            if not isinstance(user_message_count, int):
                user_message_count = 0

            try:
                result = await self.graph.ainvoke(
                    {
                        "messages": [HumanMessage(content=chat_in.user_input)],
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "profile_text": profile_text,
                        "prompt_scene": prompt_scene,
                        "current_goal": current_goal,
                        "permission_level": self.permission_level,
                    },
                    config=config,
                )
            except Exception:
                logger.exception("Graph 调用失败，回滚本轮用户消息: msg_id=%s", user_msg.id)
                try:
                    await asyncio.to_thread(
                        msg_crud.delete_conversation_message,
                        self.db,
                        user_msg.id,
                    )
                except Exception:
                    logger.exception("回滚用户消息失败: msg_id=%s", user_msg.id)
                try:
                    await self._rollback_checkpoint_state(config, checkpoint_snapshot)
                except Exception:
                    logger.exception(
                        "Graph 失败后回滚 checkpoint 失败: conv=%s",
                        conversation_id,
                    )
                raise

            # 遍历本轮严格新增的消息，分类持久化
            final_msg = await self._persist_new_messages(
                result, history_len, conversation_id
            )

            try:
                await self._maybe_compact_after_response(
                    config=config,
                    conversation_id=conversation_id,
                    result=result,
                    current_goal=current_goal,
                )
            except Exception:
                logger.exception(
                    "compact 后处理失败，保留主回复返回: conv=%s", conversation_id
                )

            # 归一化：is_edit 为兼容旧字段，skip_side_effects 优先
            skip_side_effects = chat_in.skip_side_effects or chat_in.is_edit

            # 后台任务调度
            self._schedule_side_effects(
                skip_side_effects, user_message_count, chat_in, conversation_id, user_id
            )

            # 提取最终回复文本用于接口返回
            final_content = self._extract_ai_content(final_msg)

            return ChatResponse(
                response=final_content,
                conversation_id=conversation_id,
            )
        finally:
            await self._release_conversation_lock(conversation_id, lock_token)

    async def _persist_new_messages(
        self,
        result: dict,
        history_len: int,
        conversation_id: int,
    ) -> AIMessage:
        """校验 Graph 返回结果并持久化本轮新增消息，返回最终 AIMessage。"""
        # 兜底检查：确保 messages 非空且最后一条是 AIMessage
        messages = result.get("messages")
        if not messages or not isinstance(messages, list):
            logger.error("Graph 返回异常: messages=%s", messages)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI 回复生成异常",
            )

        final_msg = messages[-1]
        if not isinstance(final_msg, AIMessage):
            logger.error(
                "Graph 返回的最后一条消息不是 AIMessage: type=%s", type(final_msg)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI 回复生成异常",
            )

        result_messages = result.get("messages") or []
        if history_len <= len(result_messages):
            candidate_messages = result_messages[history_len:]
        else:
            logger.warning(
                "Graph messages length shrank: history_len=%s result_len=%s",
                history_len,
                len(result_messages),
            )
            candidate_messages = self._extract_current_turn_messages(result_messages)

        for msg in candidate_messages:
            if isinstance(msg, HumanMessage):
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

        return final_msg

    async def _should_compact(self, result: dict) -> bool:
        """判断当前上下文是否达到 compact 阈值。"""
        messages = result.get("messages") or []
        if not messages:
            return False
        system_prompt = render_chat_system_prompt(
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scene=result.get("prompt_scene"),
            profile_text=result.get("profile_text"),
            current_goal=result.get("current_goal"),
            permission_level=self.permission_level,
        )
        token_messages = [SystemMessage(content=system_prompt), *messages]
        try:
            token_count = await asyncio.to_thread(
                get_llm_client().get_num_tokens_from_messages,
                token_messages,
            )
        except Exception:
            logger.exception("统计上下文 token 失败，跳过 compact")
            return False
        threshold = int(self._MAIN_CONTEXT_WINDOW_TOKENS * self._COMPACT_THRESHOLD_RATIO)
        return token_count >= threshold

    async def _generate_compact_summary(self, transcript: str) -> str | None:
        """调用 small model 生成 compact summary，失败时重试一次。"""
        if not transcript.strip():
            return None
        prompt = render_context_compact_prompt(transcript)
        for attempt in range(2):
            try:
                response = await get_llm_small_client().ainvoke([
                    SystemMessage(content=prompt),
                ])
                summary = response.content.strip() if isinstance(response.content, str) else ""
                if not summary:
                    logger.debug("compact summary 为空，准备重试: attempt=%s", attempt + 1)
                    continue
                return self._safe_truncate(summary, self._COMPACT_SUMMARY_MAX_CHARS)
            except Exception:
                if attempt == 1:
                    logger.exception("compact summary 生成失败，已重试")
                else:
                    logger.debug("compact summary 生成失败，准备重试", exc_info=True)
        return None

    async def _persist_compact_summary(
        self,
        conversation_id: int,
        summary: str,
        retained_messages: list,
    ) -> ConversationMessage:
        """将真实 compact summary 入库，但默认通过 API 脱敏展示。"""
        return await asyncio.to_thread(
            msg_crud.create_conversation_message,
            self.db,
            conversation_id,
            "assistant",
            summary,
            metadata={
                "compact_summary": True,
                "display": True,
                "retained_messages": [
                    self._serialize_lc_message(m) for m in retained_messages
                ],
            },
        )

    async def _apply_compact_summary(
        self,
        config: dict,
        summary: str,
        retained_messages: list,
        current_goal: str | None,
    ) -> None:
        """用 compact summary 和最新一轮消息替换 checkpoint 历史。"""
        compact_message = AIMessage(
            content=summary,
            additional_kwargs={"compact_summary": True},
        )
        await self.graph.aupdate_state(
            config,
            {
                "messages": [
                    RemoveMessage(id=REMOVE_ALL_MESSAGES),
                    compact_message,
                    *retained_messages,
                ],
                "current_goal": current_goal,
            },
        )

    async def _maybe_compact_after_response(
        self,
        config: dict,
        conversation_id: int,
        result: dict,
        current_goal: str | None,
    ) -> bool:
        """主回复完成后按阈值执行 compact。"""
        try:
            if not await self._should_compact(result):
                return False

            messages = result.get("messages") or []
            transcript, retained_messages = self._build_compact_payload(messages)
            summary = await self._generate_compact_summary(transcript)
            if not summary:
                logger.warning(
                    "compact 未生成有效摘要，保留原 checkpoint: conv=%s",
                    conversation_id,
                )
                return False

            compact_msg = await self._persist_compact_summary(
                conversation_id, summary, retained_messages
            )
            try:
                await self._apply_compact_summary(
                    config=config,
                    summary=summary,
                    retained_messages=retained_messages,
                    current_goal=current_goal,
                )
            except Exception:
                # checkpoint 更新失败时回滚 DB 写入，避免两条历史线分叉
                logger.exception(
                    "checkpoint 更新失败，回滚 compact 消息: conv=%s", conversation_id
                )
                try:
                    await asyncio.to_thread(
                        msg_crud.delete_conversation_message,
                        self.db,
                        compact_msg.id,
                    )
                except Exception:
                    logger.exception(
                        "回滚 compact 消息失败: conv=%s, msg_id=%s",
                        conversation_id,
                        compact_msg.id,
                    )
                return False
        except Exception:
            logger.exception("compact 执行失败，保留原 checkpoint: conv=%s", conversation_id)
            return False
        logger.info("AI 对话上下文已 compact: conv=%s", conversation_id)
        return True

    def _schedule_side_effects(
        self,
        skip_side_effects: bool,
        user_message_count: int,
        chat_in: ChatRequest,
        conversation_id: int,
        user_id: int,
    ) -> None:
        """调度后台任务：标题生成与用户画像更新。"""
        if skip_side_effects:
            return

        self._background_tasks.create_task(
            self._run_in_new_session(
                self._ensure_title_async, chat_in, conversation_id
            ),
            name="chat.ensure_title",
        )

        if (
            user_message_count > 0
            and user_message_count % self._PROFILE_UPDATE_INTERVAL == 0
        ):
            self._background_tasks.create_task(
                self._run_in_new_session(
                    self._maybe_update_profile_async, user_id, conversation_id
                ),
                name="chat.update_profile",
            )

    async def _run_in_new_session(self, method, *args) -> None:
        """在新 Session 中异步运行指定方法，用于后台任务隔离。"""
        try:
            with SessionLocal() as db:
                service = ChatService(db, permission_level=self.permission_level)
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
        """智能生成或更新对话标题。新对话立即生成，已有对话超时后重新生成。"""
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
        """获取对话并校验权限，不存在抛 404，无权限抛 403。"""
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
        """获取当前用户的对话列表（按最近时间倒序）。"""
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
        """获取对话消息列表。默认过滤隐藏消息，include_hidden=True 时返回完整流。"""
        await asyncio.to_thread(
            self.get_conversation_if_owned, conversation_id, user_id
        )

        # include_hidden 权限校验下沉到 Service 层
        if include_hidden and self.permission_level < 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看隐藏消息",
            )

        if include_hidden:
            # 管理员排查模式：返回完整消息流，按原始消息分页
            messages = await asyncio.to_thread(
                msg_crud.list_conversation_messages,
                self.db,
                conversation_id,
                skip,
                limit,
            )
        else:
            # 默认模式：先过滤可见消息，再分页，避免 hidden 消息占用分页配额
            messages = await asyncio.to_thread(
                msg_crud.list_visible_conversation_messages,
                self.db,
                conversation_id,
                skip,
                limit,
            )

        return [
            self._to_message_response(m, include_hidden=include_hidden)
            for m in messages
        ]

    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """物理删除对话，并清理 Checkpointer。"""
        conv = await asyncio.to_thread(
            conv_crud.get_ai_conversation_by_id, self.db, conversation_id
        )
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
        _require_owner(conv, user_id)

        # 先删除数据库记录，成功后再清理 Redis checkpoint
        await asyncio.to_thread(
            conv_crud.delete_ai_conversation, self.db, conversation_id
        )
        try:
            await delete_checkpoint(str(conversation_id))
        except Exception:
            logger.exception("清理 AI 对话 checkpoint 失败: conv=%s", conversation_id)
