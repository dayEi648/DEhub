import asyncio
import logging
import uuid
from typing import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
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
    ) -> AsyncGenerator[str, None]:
        """
        流式对话入口。

        通过 LangGraph astream_events 获取 token 级流式事件，
        yield 每个文本片段。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID（None 则新建）
            content: 用户输入内容

        Yields:
            str: LLM 生成的文本增量
        """
        messages = [HumanMessage(content=content)]

        # thread_id 用于 Checkpointer 隔离对话状态
        # 已有对话直接使用 conversation_id；新对话使用临时 UUID 避免并发冲突
        temp_thread_id = None
        if conversation_id:
            thread_id = str(conversation_id)
        else:
            temp_thread_id = f"new-{uuid.uuid4().hex}"
            thread_id = temp_thread_id

        # 已有对话：优先使用 Redis checkpoint，若已过期则从数据库加载历史
        if conversation_id is not None:
            checkpoint = await self._checkpointer.aget(
                {"configurable": {"thread_id": thread_id}}
            )
            if checkpoint is None:
                # checkpoint 过期，从数据库加载历史消息
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
                        kwargs = {"content": msg.content}
                        if msg.meta and msg.meta.get("tool_calls"):
                            kwargs["tool_calls"] = msg.meta["tool_calls"]
                        history_messages.append(AIMessage(**kwargs))
                    elif msg.role == "tool":
                        tool_call_id = ""
                        if msg.meta and msg.meta.get("tool_call_id"):
                            tool_call_id = msg.meta["tool_call_id"]
                        history_messages.append(
                            ToolMessage(content=msg.content, tool_call_id=tool_call_id)
                        )
                messages = _truncate_messages(history_messages + messages)

        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": messages,
            "title_prompt": content,
        }

        config = {"configurable": {"thread_id": thread_id, "db": self.db}}

        try:
            seen_stream = False
            total_length = 0
            max_output = settings.LLM_MAIN_MAX_OUTPUT_CHARS

            async for event in self._graph.astream_events(
                initial_state, config, version="v2"
            ):
                # 捕获 LLM token 级流式事件
                if event["event"] == "on_chat_model_stream":
                    seen_stream = True
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        if total_length + len(chunk.content) > max_output:
                            logger.warning(
                                "LLM 输出超过最大字符数限制 %s，截断", max_output
                            )
                            break
                        total_length += len(chunk.content)
                        yield chunk.content

                # 捕获 Graph 节点结束事件
                if event["event"] == "on_chain_end":
                    node_name = event.get("metadata", {}).get("langgraph_node", "")

                    # model 节点：兜底输出（未触发流式事件时）
                    # 注意：on_chain_end 会在多个层级触发（LLM 级别和节点级别），
                    # 只有节点级别的 output 是 dict 且含 "messages" 键
                    if node_name == "model":
                        output = event["data"].get("output", {})
                        if isinstance(output, dict) and "messages" in output:
                            msgs = output["messages"]
                            if msgs and isinstance(msgs[-1], AIMessage):
                                msg = msgs[-1]
                                # 仅在未出现流式事件时输出，避免重复
                                if (
                                    msg.content
                                    and not msg.tool_calls
                                    and not seen_stream
                                ):
                                    yield msg.content
                            seen_stream = False

                    # prepare 节点：获取新创建的 conversation_id
                    elif node_name == "prepare":
                        output = event["data"].get("output", {})
                        if isinstance(output, dict) and "conversation_id" in output:
                            new_id = str(output["conversation_id"])
                            config["configurable"]["thread_id"] = new_id
                            # 若使用过临时 thread_id，清理该 checkpoint 避免残留
                            if temp_thread_id and temp_thread_id != new_id:
                                await self._checkpointer.delete_checkpoint(
                                    temp_thread_id
                                )
                            # 向前端回传新创建的 conversation_id
                            yield f"__META__:conversation_id={new_id}"

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
