import asyncio
import logging
from typing import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.infrastructure.langchain_adapter import CustomChatModel
from app.infrastructure.llm_client import get_llm_client, get_llm_small_client
from app.infrastructure.redis_checkpoint import RedisCheckpointSaver
from app.graphs.chat_graph import build_chat_graph

logger = logging.getLogger(__name__)


class ChatGraphService:
    """
    LangGraph 对话服务：封装 Graph 编译实例、Checkpointer 和流式调用。

    Graph 编译结果在模块级缓存，每个请求复用同一个编译图，
    数据库会话通过 RunnableConfig 的 configurable 字段注入节点。
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self._checkpointer = RedisCheckpointSaver()
        self._llm = CustomChatModel(get_llm_client())
        self._llm_small = CustomChatModel(get_llm_small_client())
        self._graph = build_chat_graph(
            llm=self._llm,
            llm_small=self._llm_small,
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
        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "system_prompt": system_prompt,
            "messages": [HumanMessage(content=content)],
            "title_prompt": content,
        }

        # thread_id 用于 Checkpointer 隔离对话状态
        # 若 conversation_id 为 None，Graph 的 prepare 节点会创建新对话并更新 state
        thread_id = str(conversation_id) if conversation_id else "new"
        config = {"configurable": {"thread_id": thread_id, "db": self.db}}

        try:
            async for event in self._graph.astream_events(
                initial_state, config, version="v2"
            ):
                # 捕获 LLM token 级流式事件
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield chunk.content

                # 捕获 Graph 节点输出，获取新创建的 conversation_id
                # 以便前端知道新对话的 ID
                if event["event"] == "on_chain_end" and event.get("name") == "prepare":
                    output = event["data"].get("output", {})
                    if "conversation_id" in output:
                        # 新对话创建成功，更新 thread_id 以供后续 checkpoint 使用
                        config["configurable"]["thread_id"] = str(
                            output["conversation_id"]
                        )

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

        conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
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

        conv_crud.soft_delete_ai_conversation(self.db, conversation_id)
        self.db.commit()

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
        conv = self.get_conversation_or_raise(conversation_id, user_id)
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
