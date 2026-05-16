import asyncio
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app.crud import user_memory_embedding as mem_crud
from app.crud.conversation_message import list_conversation_messages
from app.infrastructure.embedding_client import get_embedding_client
from app.infrastructure.llm_client import get_llm_small_client
from app.prompts.chat_prompts import CONVERSATION_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class UserMemoryService:
    """
    用户长期记忆服务。

    负责对话摘要生成（用户画像导向）和记忆清理。
    不再存储逐轮 turn 记录，只保留对话级别的画像摘要。
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # 公开接口：摘要同步
    # ------------------------------------------------------------------

    async def sync_conversation_summary_async(
        self, user_id: int, conversation_id: int
    ) -> None:
        """
        读取当前对话的全部消息，用 small LLM 生成用户画像摘要，
        向量化后写入长期记忆（memory_type='summary'）。

        生成成功后会先清空该对话的旧 summary，再写入新摘要，
        确保向量库中每对话只保留一条画像记录。

        所有数据库操作在同一事务中完成，失败时回滚。

        Args:
            user_id: 用户 ID
            conversation_id: 对话 ID
        """
        try:
            messages = await asyncio.to_thread(
                list_conversation_messages,
                self.db,
                conversation_id,
                skip=0,
                limit=None,
            )
            if not messages:
                return

            transcript = "\n".join(
                f"{msg.role}: {msg.content}" for msg in messages
            )

            response = await get_llm_small_client().ainvoke([
                SystemMessage(content=CONVERSATION_SUMMARY_PROMPT),
                HumanMessage(content=transcript),
            ])
            summary = (
                response.content.strip()
                if isinstance(response.content, str)
                else ""
            )
            if not summary:
                logger.warning(
                    "画像摘要为空: user=%s conv=%s", user_id, conversation_id
                )
                return

            embeddings = await get_embedding_client().aembed_documents([summary])
            if not embeddings:
                logger.warning("Embedding API 返回空结果")
                return
            embedding = embeddings[0]

            # 在同一事务中删除旧画像并插入新画像
            await asyncio.to_thread(
                mem_crud.delete_memories_by_conversation,
                self.db,
                conversation_id,
                commit=False,
            )
            await asyncio.to_thread(
                mem_crud.create_memory_embedding,
                self.db,
                user_id=user_id,
                conversation_id=conversation_id,
                memory_type="summary",
                content_text=summary,
                embedding=embedding,
                commit=False,
            )
            await asyncio.to_thread(self.db.commit)
            logger.info(
                "已同步画像摘要: user=%s conv=%s", user_id, conversation_id
            )
        except Exception:
            await asyncio.to_thread(self.db.rollback)
            logger.exception(
                "同步画像摘要失败: user=%s conv=%s", user_id, conversation_id
            )

    # ------------------------------------------------------------------
    # 公开接口：清理
    # ------------------------------------------------------------------

    def delete_conversation_memories(self, conversation_id: int) -> None:
        """
        删除指定对话的所有向量记忆（管理后台彻底清理时调用）。

        注意：日常删除对话时不会调用此方法，因为 summary 是长期记忆，
        应该保留在向量库中供后续检索使用。

        Args:
            conversation_id: 对话 ID
        """
        try:
            deleted = mem_crud.delete_memories_by_conversation(
                self.db, conversation_id
            )
            if deleted:
                logger.info("已删除对话 %s 的 %s 条记忆", conversation_id, deleted)
        except Exception:
            logger.exception("删除对话 %s 记忆失败", conversation_id)
