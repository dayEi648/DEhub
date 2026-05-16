"""user_memory_service 单元测试。"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.user_memory_service import UserMemoryService


class TestSyncConversationSummaryAsync:
    """测试 sync_conversation_summary_async 的事务行为。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = UserMemoryService(self.mock_db)

    @pytest.mark.asyncio
    @patch("app.services.user_memory_service.SessionLocal")
    @patch("app.services.user_memory_service.list_conversation_messages")
    @patch("app.services.user_memory_service.get_llm_small_client")
    @patch("app.services.user_memory_service.get_embedding_client")
    @patch("app.services.user_memory_service.mem_crud.delete_memories_by_conversation")
    @patch("app.services.user_memory_service.mem_crud.create_memory_embedding")
    async def test_success_deletes_old_and_creates_new(
        self,
        mock_create,
        mock_delete,
        mock_get_embed,
        mock_get_llm,
        mock_list_msgs,
        mock_session_local,
    ):
        """成功时应在新 Session 中先删除旧记录再插入新记录，最后 commit。"""
        mock_session = MagicMock()
        mock_session_local.return_value.__enter__ = MagicMock(return_value=mock_session)
        mock_session_local.return_value.__exit__ = MagicMock(return_value=False)

        # mock messages
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.content = "你好"
        mock_list_msgs.return_value = [mock_msg]

        # mock LLM response
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="用户友好且热情。")
        )
        mock_get_llm.return_value = mock_llm

        # mock embedding
        mock_embed = MagicMock()
        mock_embed.aembed_documents = AsyncMock(return_value=[[0.1] * 1024])
        mock_get_embed.return_value = mock_embed

        await self.service.sync_conversation_summary_async(user_id=1, conversation_id=10)

        # 验证新 Session 被创建，且 delete 和 create 都在新 Session 上执行
        mock_session_local.assert_called_once()
        mock_delete.assert_called_once_with(mock_session, 10, commit=False)
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs.get("commit") is False
        # 验证 commit 在新 Session 上被调用
        mock_session.commit.assert_called_once()
        # 验证旧 Session 未被操作
        self.mock_db.commit.assert_not_called()
        self.mock_db.rollback.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.user_memory_service.list_conversation_messages")
    @patch("app.services.user_memory_service.get_llm_small_client")
    async def test_failure_does_not_persist(
        self, mock_get_llm, mock_list_msgs
    ):
        """embedding 阶段失败时不应调用持久化逻辑。"""
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_msg.content = "你好"
        mock_list_msgs.return_value = [mock_msg]

        # mock LLM 成功
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="用户友好且热情。")
        )
        mock_get_llm.return_value = mock_llm

        # mock embedding 失败
        with patch(
            "app.services.user_memory_service.get_embedding_client"
        ) as mock_get_embed:
            mock_embed = MagicMock()
            mock_embed.aembed_documents = AsyncMock(side_effect=RuntimeError("API 错误"))
            mock_get_embed.return_value = mock_embed

            await self.service.sync_conversation_summary_async(
                user_id=1, conversation_id=10
            )

        # 失败时不会调用旧 Session 的 rollback（新 Session 在 _save_summary 内部自行管理）
        self.mock_db.rollback.assert_not_called()
        self.mock_db.commit.assert_not_called()
