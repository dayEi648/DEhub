from app.graphs.builders.chat_builder import build_chat_graph
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.ai_conversation import AIConversation
from fastapi import HTTPException, status
from app.crud import ai_conversation as conv_crud
from app.crud import conversation_message as msg_crud
import asyncio



def _require_owner(conv: AIConversation, user_id: int) -> None:
    """校验当前用户是否为对话所有者。"""
    if conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该对话",
        )


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.graph = build_chat_graph()

    def chat(self, chat_in: ChatRequest, user_id: int) -> ChatResponse:
        """
        对话服务
        Args:
            chat_in: ChatRequest
            user_id: 当前用户ID
        Returns:
            ChatResponse: 对话结果
        """
        # 无 conversation_id 时自动创建新对话
        if chat_in.conversation_id is None:
            conv = conv_crud.create_ai_conversation(
                self.db,
                user_id=user_id,
                title=chat_in.user_input[:20],
            )
            conversation_id = conv.id
        else:
            conversation_id = chat_in.conversation_id

        # 持久化用户消息
        msg_crud.create_conversation_message(
            self.db, conversation_id, "user", chat_in.user_input
        )

        config = {"configurable": {"thread_id": conversation_id}}

        result = self.graph.invoke(
            {"messages": [HumanMessage(content=chat_in.user_input)]},
            config=config,
        )

        ai_content = result["messages"][-1].content

        # 持久化 AI 回复
        msg_crud.create_conversation_message(
            self.db, conversation_id, "assistant", ai_content
        )

        return ChatResponse(
            response=ai_content,
            conversation_id=conversation_id,
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
        conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
        if conv is None or conv.is_deleted:
            return None
        _require_owner(conv, user_id)
        return conv

    async def list_conversations(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[AIConversation], int]:
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
        self, conversation_id: int, user_id: int, skip: int = 0, limit: int = 100
    ) -> list:
        """
        获取对话消息列表
        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            skip: 跳过数量
            limit: 限制数量
        Returns:
            list
        """
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
    
    async def delete_conversation(self, conversation_id: int, user_id: int) -> None:
        """
        软删除对话，同时清理 Checkpointer。

        Args:
            conversation_id: 对话 ID
            user_id: 用户 ID
        """
        conv = await asyncio.to_thread(
            conv_crud.get_ai_conversation_by_id, self.db, conversation_id
        )
        if conv is None or conv.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="对话不存在",
            )
        _require_owner(conv, user_id)

        # 先清理内存 checkpoint，再软删除 DB 记录
        await asyncio.to_thread(
            self.graph.checkpointer.delete_thread, str(conversation_id)
        )
        await asyncio.to_thread(
            conv_crud.soft_delete_ai_conversation, self.db, conversation_id
        )