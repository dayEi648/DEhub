import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.crud.conversation_message import get_recent_conversation_messages
from app.crud.user_memory_embedding import (
    create_memory_embedding,
    delete_memories_by_conversation,
    delete_summary_by_conversation,
    search_user_memories,
)
from app.db.session import SessionLocal
from app.core.config import settings
from app.infrastructure.embedding_client import get_embedding_client
from app.infrastructure.llm_client import get_llm_small_client
from app.models.user_memory_embedding import UserMemoryEmbedding
from app.prompts.chat_prompts import CONVERSATION_SUMMARY

logger = logging.getLogger(__name__)

_RETENTION_DAYS = 180


class UserMemoryService:
    """
    用户长期记忆服务。

    负责对话轮次的向量化存储、对话摘要生成、以及基于语义相似度的记忆检索。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 公开接口：记忆同步
    # ------------------------------------------------------------------

    async def sync_turn_memory(
        self,
        user_id: int,
        conversation_id: int,
        user_content: str,
        assistant_content: str,
    ) -> None:
        """
        将一轮对话（用户+AI）向量化并写入长期记忆。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
            user_content: 用户消息内容
            assistant_content: AI 回复内容
        """
        text = f"用户: {user_content}\n助手: {assistant_content}"
        try:
            embedding = await get_embedding_client().aembed_single(text)
            await asyncio.to_thread(
                create_memory_embedding,
                self.db,
                user_id,
                conversation_id,
                "turn",
                text,
                embedding,
            )
            logger.info(
                "已同步用户 %s 对话 %s 的 turn 记忆", user_id, conversation_id
            )
        except Exception:
            logger.exception(
                "同步 turn 记忆失败: user=%s conv=%s", user_id, conversation_id
            )

    async def sync_conversation_summary(
        self, user_id: int, conversation_id: int
    ) -> None:
        """
        读取当前对话最近 20 条消息，用 llm_small 生成累积摘要，
        向量化后写入长期记忆（memory_type='summary'）。

        每对话只保留最新摘要，旧摘要会被覆盖。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
        """
        try:
            messages = await asyncio.to_thread(
                get_recent_conversation_messages,
                self.db,
                conversation_id,
                limit=20,
            )
            if not messages:
                return

            transcript = "\n".join(
                f"{msg.role}: {msg.content}" for msg in messages
            )

            summary = await get_llm_small_client().achat(
                messages=[{"role": "user", "content": transcript}],
                system_prompt=CONVERSATION_SUMMARY,
            )
            summary = summary.strip()
            if not summary:
                logger.warning(
                    "摘要生成结果为空: user=%s conv=%s", user_id, conversation_id
                )
                return

            embedding = await get_embedding_client().aembed_single(summary)

            # 先删除该对话旧摘要，再插入新摘要
            await asyncio.to_thread(
                delete_summary_by_conversation, self.db, conversation_id
            )
            await asyncio.to_thread(
                create_memory_embedding,
                self.db,
                user_id,
                conversation_id,
                "summary",
                summary,
                embedding,
            )
            logger.info(
                "已同步用户 %s 对话 %s 的 summary 记忆", user_id, conversation_id
            )
        except Exception:
            logger.exception(
                "同步 summary 记忆失败: user=%s conv=%s", user_id, conversation_id
            )

    # ------------------------------------------------------------------
    # 公开接口：记忆检索
    # ------------------------------------------------------------------

    async def search_relevant_memories(
        self,
        user_id: int,
        query: str,
        top_k: int = 3,
        exclude_conversation_id: int | None = None,
        min_similarity: float = settings.RAG_MIN_SIMILARITY,
    ) -> list[UserMemoryEmbedding]:
        """
        检索某用户半年内与当前问题最相关的长期记忆。

        Args:
            user_id: 用户 ID
            query: 用户当前输入文本
            top_k: 返回结果数量上限
            exclude_conversation_id: 排除的对话 ID（通常为当前对话，避免自我污染）
            min_similarity: 最小相似度阈值，低于此值的结果会被过滤

        Returns:
            list[UserMemoryEmbedding]: 按相似度排序的记忆记录列表
        """
        if not query or not query.strip():
            return []

        try:
            query_embedding = await get_embedding_client().aembed_single(query)
            since = (
                datetime.now(timezone.utc) - timedelta(days=_RETENTION_DAYS)
            ).isoformat()

            results = await asyncio.to_thread(
                search_user_memories,
                self.db,
                user_id,
                query_embedding,
                since,
                top_k,
                exclude_conversation_id,
            )
            filtered: list[UserMemoryEmbedding] = []
            for record, distance in results:
                similarity = max(0.0, 1.0 - float(distance))
                if similarity >= min_similarity:
                    filtered.append(record)
            return filtered
        except Exception:
            logger.exception("检索用户 %s 长期记忆失败", user_id)
            return []

    # ------------------------------------------------------------------
    # 公开接口：清理
    # ------------------------------------------------------------------

    async def delete_conversation_memories(self, conversation_id: int) -> None:
        """
        删除指定对话的所有长期记忆（对话删除时调用）。

        Args:
            conversation_id: 对话 ID
        """
        try:
            deleted = await asyncio.to_thread(
                delete_memories_by_conversation, self.db, conversation_id
            )
            if deleted:
                logger.info(
                    "已删除对话 %s 的 %s 条记忆", conversation_id, deleted
                )
        except Exception:
            logger.exception("删除对话 %s 记忆失败", conversation_id)


# ------------------------------------------------------------------
# 模块级辅助：用于 API 层 BackgroundTasks 的独立实例
# ------------------------------------------------------------------

async def delete_conversation_memories_task(conversation_id: int) -> None:
    """
    独立后台任务：删除指定对话的长期记忆。

    供 FastAPI BackgroundTasks 调用。
    """
    db = SessionLocal()
    try:
        service = UserMemoryService(db)
        await service.delete_conversation_memories(conversation_id)
    finally:
        await asyncio.to_thread(db.close)
