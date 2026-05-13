from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.graphs.chat_graph import _build_system_prompt, _format_memories
from app.models.user_memory_embedding import UserMemoryEmbedding
from app.services.user_memory_service import UserMemoryService


class TestFormatMemories:
    """测试记忆格式化逻辑"""

    def test_empty_memories(self):
        """空记忆列表应返回空列表"""
        assert _format_memories([]) == []

    def test_single_summary(self):
        """单条 summary 记忆应正确格式化"""
        mem = MagicMock(spec=UserMemoryEmbedding)
        mem.memory_type = "summary"
        mem.content_text = "用户喜欢Python编程"
        result = _format_memories([mem])
        assert any("[对话摘要]" in item for item in result)
        assert any("用户喜欢Python编程" in item for item in result)

    def test_single_turn(self):
        """单条 turn 记忆应正确格式化"""
        mem = MagicMock(spec=UserMemoryEmbedding)
        mem.memory_type = "turn"
        mem.content_text = "用户: 你好\n助手: 你好"
        result = _format_memories([mem])
        assert any("[历史对话]" in item for item in result)

    def test_multiple_memories(self):
        """多条记忆应返回多条格式化文本"""
        mem1 = MagicMock(spec=UserMemoryEmbedding)
        mem1.memory_type = "summary"
        mem1.content_text = "摘要1"
        mem2 = MagicMock(spec=UserMemoryEmbedding)
        mem2.memory_type = "turn"
        mem2.content_text = "turn1"
        result = _format_memories([mem1, mem2])
        assert len(result) == 2
        assert any("摘要1" in item for item in result)
        assert any("turn1" in item for item in result)


class TestBuildSystemPrompt:
    """测试 System Prompt 拼接逻辑"""

    def test_no_memory_no_original(self):
        """无记忆无原始 system prompt 时应返回 None"""
        assert _build_system_prompt(None, "") is None

    def test_no_memory_with_original(self):
        """无记忆但有原始 system prompt 时应返回原始值"""
        assert _build_system_prompt("原始提示", "") == "原始提示"

    def test_memory_no_original(self):
        """有记忆但无原始 system prompt 时应只返回记忆部分"""
        result = _build_system_prompt(None, ["记忆内容"])
        assert "记忆内容" in result
        assert "历史记忆" in result

    def test_memory_with_original(self):
        """有记忆且有原始 system prompt 时应正确拼接"""
        result = _build_system_prompt("原始提示", ["记忆内容"])
        assert "原始提示" in result
        assert "记忆内容" in result
        assert "\n\n" in result


class TestUserMemoryServiceSyncTurn:
    """测试 turn 记忆同步（使用 mock 隔离外部依赖）"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserMemoryService(mock_db)

    @pytest.fixture
    def mock_embedding_client(self):
        mock = MagicMock()
        mock.aembed_single = AsyncMock(return_value=[0.0] * 1024)
        return mock

    @pytest.mark.asyncio
    async def test_sync_turn_success(self, service, mock_embedding_client):
        """正常情况应调用 embedding 并写入 DB"""
        with patch(
            "app.services.user_memory_service.get_embedding_client",
            return_value=mock_embedding_client,
        ), patch(
            "app.services.user_memory_service.create_memory_embedding"
        ) as mock_create:
            await service.sync_turn_memory(1, 10, "用户问题", "助手回答")
            mock_embedding_client.aembed_single.assert_awaited_once()
            mock_create.assert_called_once()
            # asyncio.to_thread 传递的是位置参数
            args = mock_create.call_args[0]
            assert args[3] == "turn"  # memory_type
            assert "用户问题" in args[4]  # content_text
            assert "助手回答" in args[4]

    @pytest.mark.asyncio
    async def test_sync_turn_failure_graceful(self, service):
        """embedding 失败时不应抛异常"""
        mock_client = MagicMock()
        mock_client.aembed_single = AsyncMock(side_effect=Exception("API 错误"))
        with patch(
            "app.services.user_memory_service.get_embedding_client",
            return_value=mock_client,
        ):
            # 不应抛出异常
            await service.sync_turn_memory(1, 10, "用户问题", "助手回答")


class TestUserMemoryServiceSearch:
    """测试记忆检索"""

    @pytest.fixture
    def service(self):
        db = MagicMock()
        return UserMemoryService(db)

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, service):
        """空查询应直接返回空列表"""
        result = await service.search_relevant_memories(1, "", top_k=3)
        assert result == []

    @pytest.mark.asyncio
    async def test_search_success(self, service):
        """正常检索应返回格式化结果"""
        mock_embedding = MagicMock()
        mock_embedding.aembed_single = AsyncMock(return_value=[0.1] * 1024)

        mem1 = MagicMock(spec=UserMemoryEmbedding)
        mem1.memory_type = "summary"
        mem1.content_text = "用户喜欢Python"

        with patch(
            "app.services.user_memory_service.get_embedding_client",
            return_value=mock_embedding,
        ), patch(
            "app.services.user_memory_service.search_user_memories",
            return_value=[(mem1, 0.2)],
        ):
            result = await service.search_relevant_memories(1, "Python", top_k=3)
            assert len(result) == 1
            assert result[0].content_text == "用户喜欢Python"


class TestUserMemoryServiceDelete:
    """测试记忆清理"""

    @pytest.fixture
    def service(self):
        db = MagicMock()
        return UserMemoryService(db)

    @pytest.mark.asyncio
    async def test_delete_conversation_memories(self, service):
        """应调用 delete_memories_by_conversation 并返回删除数量"""
        with patch(
            "app.services.user_memory_service.delete_memories_by_conversation",
            return_value=5,
        ) as mock_delete:
            await service.delete_conversation_memories(10)
            mock_delete.assert_called_once()
