from datetime import datetime, timezone
from app.graphs.builders.chat_builder import build_chat_graph
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, SystemMessage
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.ai_conversation import AIConversation
from fastapi import HTTPException, status
from app.crud import ai_conversation as conv_crud
from app.crud import conversation_message as msg_crud
from app.services.user_memory_service import UserMemoryService
from app.infrastructure.llm_client import get_llm_small_client
from app.prompts.chat_prompts import CONVERSATION_TITLE_PROMPT
import asyncio


def _require_owner(conv: AIConversation, user_id: int) -> None:
    """校验当前用户是否为对话所有者。"""
    if conv.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该对话",
        )


# 每达到多少条消息就重新生成用户画像摘要
_SUMMARY_INTERVAL = 6


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.graph = build_chat_graph()
        self.memory_service = UserMemoryService(db)

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
                title="New Chat",
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
            {
                "messages": [HumanMessage(content=chat_in.user_input)],
                "user_id": user_id,
            },
            config=config,
        )

        ai_content = result["messages"][-1].content

        # 持久化 AI 回复
        msg_crud.create_conversation_message(
            self.db, conversation_id, "assistant", ai_content
        )

        # 处理标题生成（编辑消息时跳过）
        if not chat_in.is_edit:
            self._ensure_title(chat_in, conversation_id)

        # 判断是否触发画像摘要生成
        self._maybe_sync_summary(user_id, conversation_id)

        return ChatResponse(
            response=ai_content,
            conversation_id=conversation_id,
        )

    def _ensure_title(self, chat_in: ChatRequest, conversation_id: int) -> None:
        """
        智能生成或更新对话标题。

        - 新对话首次消息：立即生成标题
        - 已有对话：距上次消息超过 5 分钟则重新生成，否则只更新 last_message_at
        """
        try:
            conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
            if conv is None:
                return

            now = datetime.now(timezone.utc)
            last_at = conv.last_message_at

            # 判断是否需要重新生成标题
            should_regenerate = False
            if chat_in.conversation_id is None:
                # 新对话首次消息
                should_regenerate = True
            elif last_at is not None:
                elapsed = (now - last_at).total_seconds()
                if elapsed > 300:  # 5 分钟 = 300 秒
                    should_regenerate = True
            else:
                # 已有对话但没有 last_message_at（兼容旧数据），直接生成
                should_regenerate = True

            if should_regenerate:
                title = self._generate_title(chat_in.user_input)
                if title:
                    conv_crud.update_conversation_title(self.db, conversation_id, title)

            # 更新最后消息时间
            conv_crud.update_last_message_at(self.db, conversation_id)
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "标题生成失败: conv=%s", conversation_id
            )

    def _generate_title(self, user_input: str) -> str:
        """调用 small LLM 生成对话标题，返回空字符串表示生成失败。"""
        try:
            response = get_llm_small_client().invoke([
                SystemMessage(content=CONVERSATION_TITLE_PROMPT),
                HumanMessage(content=user_input),
            ])
            title = response.content.strip().replace('"', '').replace("'", "")
            # 截断到 20 字，防止模型失控
            return title[:20] if title else ""
        except Exception:
            return ""

    def _maybe_sync_summary(self, user_id: int, conversation_id: int) -> None:
        """
        检查当前对话消息数，若达到阈值则触发用户画像摘要生成。
        """
        try:
            conv = conv_crud.get_ai_conversation_by_id(self.db, conversation_id)
            if conv is None:
                return

            current_count = msg_crud.count_conversation_messages(
                self.db, conversation_id
            )
            last_count = conv.summary_message_count or 0

            if current_count >= _SUMMARY_INTERVAL and (
                current_count - last_count
            ) >= _SUMMARY_INTERVAL:
                self.memory_service.sync_conversation_summary(
                    user_id, conversation_id
                )
                conv_crud.update_summary_message_count(
                    self.db, conversation_id, current_count
                )
        except Exception:
            import logging

            logging.getLogger(__name__).exception(
                "判断画像摘要触发失败: conv=%s", conversation_id
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
        软删除对话，并清理 Checkpointer。
        向量库中的画像摘要会被保留，作为长期记忆供后续检索。

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

        # 清理 PostgreSQL checkpoint，再软删除 DB 记录
        from app.infrastructure.checkpoint_client import delete_checkpoint
        await delete_checkpoint(str(conversation_id))
        await asyncio.to_thread(
            conv_crud.soft_delete_ai_conversation, self.db, conversation_id
        )
