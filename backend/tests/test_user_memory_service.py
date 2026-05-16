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
    ):
        """成功时应在同一事务中先删除旧记录再插入新记录，最后 commit。"""
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

        # 验证 delete 和 create 都被调用，且 commit=False
        mock_delete.assert_called_once_with(self.mock_db, 10, commit=False)
        mock_create.assert_called_once()
        assert mock_create.call_args.kwargs.get("commit") is False
        # 验证 commit 被调用
        self.mock_db.commit.assert_called_once()
        # 验证 rollback 未被调用
        self.mock_db.rollback.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.user_memory_service.list_conversation_messages")
    @patch("app.services.user_memory_service.get_llm_small_client")
    async def test_failure_rolls_back_transaction(
        self, mock_get_llm, mock_list_msgs
    ):
        """embedding 阶段失败时应回滚事务，不删除旧记录。"""
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

        # 验证 rollback 被调用，commit 未被调用
        self.mock_db.rollback.assert_called_once()
        self.mock_db.commit.assert_not_called()
