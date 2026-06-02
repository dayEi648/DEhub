"""RAG Query 改写服务单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rag_query_service import RAGQueryService


class TestRAGQueryServiceExpandQueries:
    def setup_method(self):
        self.service = RAGQueryService()

    @pytest.mark.asyncio
    async def test_expand_queries_returns_list(self):
        """正常改写应返回包含原query的列表。"""
        mock_response = MagicMock()
        mock_response.content = (
            "Docker 容器化部署\n"
            "Docker 最佳实践\n"
            "容器技术 Docker\n"
            "如何使用 Docker\n"
            "Docker 入门教程"
        )

        mock_client = AsyncMock()
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.services.rag_query_service.create_llm_small_client",
            return_value=mock_client,
        ), patch(
            "app.services.rag_query_service.settings.RAG_QUERY_EXPANSION_ENABLED",
            True,
        ):
            result = await self.service.expand_queries("Docker 相关博客", num_queries=5)

        assert len(result) == 5
        assert "Docker 相关博客" in result
        assert "Docker 容器化部署" in result
        mock_client.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_expand_queries_disabled_returns_original(self):
        """配置关闭时应直接返回原query。"""
        with patch(
            "app.services.rag_query_service.settings.RAG_QUERY_EXPANSION_ENABLED",
            False,
        ):
            result = await self.service.expand_queries("Docker")

        assert result == ["Docker"]

    @pytest.mark.asyncio
    async def test_expand_queries_llm_failure_fallback(self):
        """LLM 调用失败时应降级返回原query。"""
        mock_client = AsyncMock()
        mock_client.ainvoke.side_effect = RuntimeError("API 超时")

        with patch(
            "app.services.rag_query_service.create_llm_small_client",
            return_value=mock_client,
        ), patch(
            "app.services.rag_query_service.settings.RAG_QUERY_EXPANSION_ENABLED",
            True,
        ):
            result = await self.service.expand_queries("Redis 缓存")

        assert result == ["Redis 缓存"]

    @pytest.mark.asyncio
    async def test_expand_queries_parse_empty_fallback(self):
        """LLM 返回空内容时应降级返回原query。"""
        mock_response = MagicMock()
        mock_response.content = ""

        mock_client = AsyncMock()
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.services.rag_query_service.create_llm_small_client",
            return_value=mock_client,
        ), patch(
            "app.services.rag_query_service.settings.RAG_QUERY_EXPANSION_ENABLED",
            True,
        ):
            result = await self.service.expand_queries("Go 语言")

        assert result == ["Go 语言"]

    @pytest.mark.asyncio
    async def test_expand_queries_parses_numbered_output(self):
        """能正确解析带编号的 LLM 输出。"""
        mock_response = MagicMock()
        mock_response.content = (
            "1. Docker 基础\n"
            "2. Docker 进阶\n"
            "3. 容器化实践\n"
            "4. Docker 与 Kubernetes\n"
            "5. Docker 最佳实践"
        )

        mock_client = AsyncMock()
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.services.rag_query_service.create_llm_small_client",
            return_value=mock_client,
        ), patch(
            "app.services.rag_query_service.settings.RAG_QUERY_EXPANSION_ENABLED",
            True,
        ):
            result = await self.service.expand_queries("Docker", num_queries=5)

        assert len(result) == 5
        assert "Docker 基础" in result
        assert "Docker 与 Kubernetes" in result
        # 确保编号被去除
        assert not any(r.startswith("1.") for r in result)

    def test_parse_expansion_output_filters_short(self):
        """过滤过短的查询。"""
        raw = "Docker\n\nGo\nPython 异步编程\n"
        result = RAGQueryService._parse_expansion_output(raw, expected_count=3)
        assert "Python 异步编程" in result
        # "Docker" 和 "Go" 只有2个字，保留（>=2）
        assert len(result) == 3

    def test_parse_expansion_output_deduplicates(self):
        """去重测试。"""
        raw = "Docker\nDocker\nKubernetes\n"
        result = RAGQueryService._parse_expansion_output(raw, expected_count=3)
        assert result.count("Docker") == 1
        assert "Kubernetes" in result
        # 不足3条时用最后一条填充
        assert result[-1] == "Kubernetes"

    def test_parse_expansion_output_empty_returns_empty(self):
        """空输入返回空列表。"""
        result = RAGQueryService._parse_expansion_output("", expected_count=5)
        assert result == []


class TestRAGQueryServiceParseExpansion:
    def test_parse_removes_quotes(self):
        """去除引号。"""
        raw = '"Docker 入门"\n「Kubernetes 基础」\n\'Go 语言\''
        result = RAGQueryService._parse_expansion_output(raw, expected_count=3)
        assert "Docker 入门" in result
        assert "Kubernetes 基础" in result
        assert "Go 语言" in result

    def test_parse_removes_bullets(self):
        """去除列表符号。"""
        raw = "- Docker\n* Kubernetes\n• Go 语言"
        result = RAGQueryService._parse_expansion_output(raw, expected_count=3)
        assert "Docker" in result
        assert "Kubernetes" in result
        assert "Go 语言" in result
