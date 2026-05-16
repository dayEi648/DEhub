"""checkpoint_client 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure import checkpoint_client as cp_client


class TestGetCheckpointer:
    """测试 get_checkpointer 防御性编程。"""

    def test_raises_when_not_initialized(self):
        """未初始化时调用 get_checkpointer 应抛出 ValueError。"""
        with patch.object(cp_client, "_checkpointer", None):
            with pytest.raises(ValueError, match="未初始化"):
                cp_client.get_checkpointer()

    def test_returns_instance_when_initialized(self):
        """已初始化时返回实例。"""
        mock_cp = MagicMock()
        with patch.object(cp_client, "_checkpointer", mock_cp):
            result = cp_client.get_checkpointer()
            assert result is mock_cp


class TestDeleteCheckpoint:
    """测试 delete_checkpoint 调用链路。"""

    @pytest.mark.asyncio
    async def test_deletes_thread_via_checkpointer(self):
        """delete_checkpoint 应正确调用 checkpointer 的 adelete_thread。"""
        mock_cp = MagicMock()
        mock_cp.adelete_thread = AsyncMock()

        with patch.object(cp_client, "_checkpointer", mock_cp):
            await cp_client.delete_checkpoint("thread_123")

        mock_cp.adelete_thread.assert_awaited_once_with("thread_123")
