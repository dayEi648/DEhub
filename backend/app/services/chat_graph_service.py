import asyncio
import logging
import uuid
from typing import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.infrastructure.llm_client import get_llm_client, get_llm_small_client
from app.infrastructure.redis_checkpoint import RedisCheckpointSaver
from app.graphs.chat_graph import build_chat_graph
from app.core.config import settings

logger = logging.getLogger(__name__)

# 历史消息最大字符数（近似上下文窗口管理）
_MAX_HISTORY_CHARS = 16000


def _truncate_messages(messages: list) -> list:
    """
    截断历史消息，使总字符数不超过阈值。

    保留最后一条用户消息，从后往前累加，超出时丢弃更早的消息。
    SystemMessage（如果存在）会被保留在头部。
    """
    if not messages:
        return messages

    # 分离 system message（如果存在）
    system_msg = None
    other_messages = []
    for msg in messages:
        if isinstance(msg, SystemMessage):
            system_msg = msg
        else:
            other_messages.append(msg)

    # 从后往前累加，保留最近的消息
    kept: list = []
    total_chars = 0
    for msg in reversed(other_messages):
        content_len = len(msg.content or "")
        if total_chars + content_len > _MAX_HISTORY_CHARS and kept:
            # 已超出且至少保留了一条，则停止
            break
        kept.insert(0, msg)
        total_chars += content_len

    result: list = []
    if system_msg:
        result.append(system_msg)
    result.extend(kept)
    return result


class ChatGraphService:
    """
    LangGraph 对话服务：封装 Graph 编译实例、Checkpointer 和流式调用。

    Graph 编译结果在模块级缓存，每个请求复用同一个编译图，
    数据库会话通过 RunnableConfig 的 configurable 字段注入节点。
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._checkpointer = RedisCheckpointSaver()
        self._llm = get_llm_client()
        self._llm_small = get_llm_small_client()
        self._graph = build_chat_graph(
            llm=self._llm,
            llm_small=self._llm_small,
            checkpointer=self._checkpointer,
        )

    async def stream_chat(
        self,
        user_id: int,
        conversation_id: int | None,
        content: str,
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话入口。

        通过 LangGraph astream_events 获取 token 级流式事件，
        yield 每个文本片段。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID（None 则新建）
            content: 用户输入内容
            system_prompt: 可选的 System Prompt

        Yields:
            str: LLM 生成的文本增量
        """
        messages = [HumanMessage(content=content)]

        if conversation_id is not None:
            # 从数据库加载历史消息，避免 Redis checkpoint 过期导致上下文丢失
            from app.crud import conversation_message as msg_crud

            history = await asyncio.to_thread(
                msg_crud.list_conversation_messages,
                self.db,
                conversation_id,
                skip=0,
                limit=50,
            )
            history_messages = []
            for msg in history:
                if msg.role == "user":
                    history_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history_messages.append(AIMessage(content=msg.content))
            messages = _truncate_messages(history_messages + messages)

        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "messages": messages,
            "title_prompt": content,
        }

        # thread_id 用于 Checkpointer 隔离对话状态
        # 已有对话直接使用 conversation_id；新对话使用临时 UUID 避免并发冲突
        temp_thread_id = None
        if conversation_id:
            thread_id = str(conversation_id)
        else:
            temp_thread_id = f"new-{uuid.uuid4().hex}"
            thread_id = temp_thread_id

        config = {"configurable": {"thread_id": thread_id, "db": self.db}}

        try:
            seen_stream = False
            async for event in self._graph.astream_events(
                initial_state, config, version="v2"
            ):
                # 捕获 LLM token 级流式事件（最终回复阶段）
                if event["event"] == "on_chat_model_stream":
                    seen_stream = True
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield chunk.content

                # 捕获 model 节点非流式输出（决策阶段直接回复，无 tool call 时）
                if event["event"] == "on_chain_end" and event.get("name") == "model":
                    output = event["data"].get("output", {})
                    msgs = output.get("messages", [])
                    if msgs and isinstance(msgs[-1], AIMessage):
                        msg = msgs[-1]
                        # 仅在未出现流式事件时输出，避免重复
                        if msg.content and not msg.tool_calls and not seen_stream:
                            yield msg.content
                    seen_stream = False

                # 捕获 Graph 节点输出，获取新创建的 conversation_id
                # 以便前端知道新对话的 ID，并切换 thread_id 供后续 checkpoint 使用
                if event["event"] == "on_chain_end" and event.get("name") == "prepare":
                    output = event["data"].get("output", {})
                    if "conversation_id" in output:
                        new_id = str(output["conversation_id"])
                        config["configurable"]["thread_id"] = new_id
                        # 若使用过临时 thread_id，清理该 checkpoint 避免残留
                        if temp_thread_id and temp_thread_id != new_id:
                            await self._checkpointer.delete_checkpoint(temp_thread_id)

        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Graph stream failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI 服务暂时不可用，请稍后重试",
            ) from exc

    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """
        软删除对话，同时清理 Checkpointer。

        长期记忆向量的清理由调用方通过 BackgroundTasks 触发。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
        """
        from app.crud import ai_conversation as conv_crud

        conv = await asyncio.to_thread(
            conv_crud.get_ai_conversation_by_id, self.db, conversation_id
        )
        if conv is None or conv.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
        if conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该对话",
            )

        await asyncio.to_thread(
            conv_crud.soft_delete_ai_conversation, self.db, conversation_id
        )
        # CRUD 内部已执行 commit，无需再次调用

        # 清理 Redis Checkpointer
        await self._checkpointer.delete_checkpoint(str(conversation_id))

    async def list_conversations(
        self, user_id: int, skip: int = 0, limit: int = 20
    ) -> tuple[list, int]:
        """列出用户的对话列表。"""
        from app.crud import ai_conversation as conv_crud

        return await asyncio.to_thread(
            conv_crud.list_ai_conversations_by_user, self.db, user_id, skip, limit
        )

    async def get_messages(
        self, conversation_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> list:
        """获取对话消息列表。"""
        from app.crud import conversation_message as msg_crud

        # 校验权限
        conv = await asyncio.to_thread(
            self.get_conversation_or_raise, conversation_id, user_id
        )
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )

        return await asyncio.to_thread(
            msg_crud.list_conversation_messages,
            self.db,
            conversation_id,
            skip,
            limit,
        )

    def get_conversation_or_raise(self, conversation_id: int, user_id: int):
        """
        获取对话并校验权限。

        - 对话不存在或已删除 → 返回 None（调用方应抛 404）
        - 对话存在但不属于当前用户 → 抛 403

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID

        Returns:
            AIConversation | None
        """
        from app.crud import ai_conversation as conv_crud
        from app.graphs.chat_graph import _require_owner

        conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
        if conv is None or conv.is_deleted:
            return None
        _require_owner(conv, user_id)
        return conv
