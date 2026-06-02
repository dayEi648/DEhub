"""联网搜索工具单元测试。"""

import asyncio
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.agent_monitoring_callback import (
    AgentMonitoringCallback,
    get_trace_buffer,
)
from app.graphs.nodes.toolnodes.web_search import (
    _deduplicate_results,
    _expand_search_queries,
    _extract_json_array,
    _format_web_search_results,
    _iqs_search_single,
    search_web,
)


# ===================================================================
# _extract_json_array
# ===================================================================

class TestExtractJsonArray:
    def test_plain_json_array(self):
        """纯 JSON 数组应被正确解析。"""
        result = _extract_json_array('["query1", "query2", "query3"]')
        assert result == ["query1", "query2", "query3"]

    def test_markdown_code_block(self):
        """markdown 代码块包裹的 JSON 应被正确解析。"""
        text = '```json\n["q1", "q2"]\n```'
        result = _extract_json_array(text)
        assert result == ["q1", "q2"]

    def test_with_extra_text(self):
        """带有额外说明文字的 JSON 应被正确提取。"""
        text = 'Here are queries:\n```\n["a", "b"]\n```\nDone.'
        result = _extract_json_array(text)
        assert result == ["a", "b"]

    def test_no_json_returns_none(self):
        """无 JSON 数组时应返回 None。"""
        assert _extract_json_array("just some text") is None

    def test_empty_text_returns_none(self):
        """空文本应返回 None。"""
        assert _extract_json_array("") is None

    def test_invalid_json_returns_none(self):
        """无效 JSON 应返回 None。"""
        assert _extract_json_array("[not valid json]") is None

    def test_non_array_json_returns_none(self):
        """非数组 JSON 应返回 None。"""
        assert _extract_json_array('{"key": "value"}') is None


# ===================================================================
# _expand_search_queries
# ===================================================================

class TestExpandSearchQueries:
    @pytest.mark.asyncio
    async def test_normal_expansion(self):
        """small 模型正常返回 JSON 数组时应解析为多个 query。"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '["q1", "q2", "q3"]'
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.graphs.nodes.toolnodes.web_search.create_llm_small_client",
            return_value=mock_client,
        ):
            result = await _expand_search_queries("original")
            assert result == ["q1", "q2", "q3"]

    @pytest.mark.asyncio
    async def test_fallback_on_json_parse_failure(self):
        """JSON 解析失败时应降级为原始 query。"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "not json at all"
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.graphs.nodes.toolnodes.web_search.create_llm_small_client",
            return_value=mock_client,
        ):
            result = await _expand_search_queries("original query")
            assert result == ["original query"]

    @pytest.mark.asyncio
    async def test_fallback_on_empty_array(self):
        """返回空数组时应降级为原始 query。"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "[]"
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.graphs.nodes.toolnodes.web_search.create_llm_small_client",
            return_value=mock_client,
        ):
            result = await _expand_search_queries("original query")
            assert result == ["original query"]

    @pytest.mark.asyncio
    async def test_fallback_on_exception(self):
        """small 模型调用异常时应降级为原始 query。"""
        mock_client = AsyncMock()
        mock_client.ainvoke.side_effect = RuntimeError("timeout")

        with patch(
            "app.graphs.nodes.toolnodes.web_search.create_llm_small_client",
            return_value=mock_client,
        ):
            result = await _expand_search_queries("original query")
            assert result == ["original query"]

    @pytest.mark.asyncio
    async def test_deduplicates_expanded_queries(self):
        """扩展结果中有重复 query 时应去重。"""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = '["q1", "q1", "q2"]'
        mock_client.ainvoke.return_value = mock_response

        with patch(
            "app.graphs.nodes.toolnodes.web_search.create_llm_small_client",
            return_value=mock_client,
        ):
            result = await _expand_search_queries("original")
            assert result == ["q1", "q2"]


# ===================================================================
# _iqs_search_single
# ===================================================================

class _MockAsyncClient:
    """同步构造、支持 async with 与 async post 的 httpx.AsyncClient mock。"""

    def __init__(self, resp: MagicMock, **kwargs):
        self._resp = resp
        self.post = AsyncMock(return_value=resp)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class TestIqsSearchSingle:
    @pytest.mark.asyncio
    async def test_payload_uses_summary_not_maintext(self):
        """IQS 请求 payload 应使用 summary=True, mainText=False。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"pageItems": []}
        mock_resp.raise_for_status = MagicMock()

        # 用于捕获实际创建的 client 实例
        created_clients: list[_MockAsyncClient] = []
        original_init = _MockAsyncClient.__init__

        def _tracking_init(self, resp, **kwargs):
            original_init(self, resp, **kwargs)
            created_clients.append(self)

        with patch.object(
            _MockAsyncClient, "__init__", _tracking_init
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.httpx.AsyncClient",
            lambda **kw: _MockAsyncClient(mock_resp, **kw),
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_NUM_RESULTS_PER_QUERY",
            5,
        ):
            await _iqs_search_single("test query")

            assert len(created_clients) == 1
            call_args = created_clients[0].post.call_args
            payload = call_args[1]["json"]
            assert payload["contents"]["summary"] is True
            assert payload["contents"]["mainText"] is False
            assert payload["numResults"] == 5

    @pytest.mark.asyncio
    async def test_returns_page_items(self):
        """API 正常返回时应提取 pageItems。"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "pageItems": [
                {"title": "t1", "link": "http://a.com"},
                {"title": "t2", "link": "http://b.com"},
            ]
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "app.graphs.nodes.toolnodes.web_search.httpx.AsyncClient",
            lambda **kw: _MockAsyncClient(mock_resp, **kw),
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ):
            result = await _iqs_search_single("q")
            assert len(result) == 2
            assert result[0]["title"] == "t1"

    @pytest.mark.asyncio
    async def test_api_error_returns_empty(self):
        """API 异常时应返回空列表。"""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        class _ErrorClient(_MockAsyncClient):
            def __init__(self, resp, **kwargs):
                super().__init__(resp, **kwargs)
                self.post = AsyncMock(side_effect=RuntimeError("network"))

        with patch(
            "app.graphs.nodes.toolnodes.web_search.httpx.AsyncClient",
            lambda **kw: _ErrorClient(mock_resp, **kw),
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ):
            result = await _iqs_search_single("q")
            assert result == []

    @pytest.mark.asyncio
    async def test_no_api_key_returns_empty(self):
        """未配置 API key 时应返回空列表。"""
        with patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "",
        ):
            result = await _iqs_search_single("q")
            assert result == []


# ===================================================================
# _deduplicate_results
# ===================================================================

class TestDeduplicateResults:
    def test_url_deduplication(self):
        """相同 URL 的结果应只保留第一条。"""
        results = [
            {"title": "A", "link": "http://same.com", "summary": "s1", "rerankScore": 0.9},
            {"title": "B", "link": "http://same.com", "summary": "s2", "rerankScore": 0.8},
            {"title": "C", "link": "http://other.com", "summary": "s3"},
        ]
        deduped = _deduplicate_results(results)
        assert len(deduped) == 2
        assert deduped[0]["title"] == "A"
        assert deduped[1]["link"] == "http://other.com"

    def test_similar_content_deduplication_keeps_higher_score(self):
        """内容高度相似时应保留 rerankScore 更高的结果。"""
        results = [
            {
                "title": "Python Tutorial",
                "link": "http://a.com",
                "summary": "Learn Python programming basics step by step.",
                "rerankScore": 0.7,
            },
            {
                "title": "Python Tutorial",
                "link": "http://b.com",
                "summary": "Learn Python programming basics step by step.",
                "rerankScore": 0.9,
            },
        ]
        deduped = _deduplicate_results(results)
        assert len(deduped) == 1
        assert deduped[0]["link"] == "http://b.com"

    def test_no_duplicates_preserve_order(self):
        """无重复结果时应保持原有顺序。"""
        results = [
            {"title": "A", "link": "http://a.com", "summary": "s1"},
            {"title": "B", "link": "http://b.com", "summary": "s2"},
            {"title": "C", "link": "http://c.com", "summary": "s3"},
        ]
        deduped = _deduplicate_results(results)
        assert len(deduped) == 3
        assert [r["title"] for r in deduped] == ["A", "B", "C"]

    def test_empty_list(self):
        """空列表应返回空列表。"""
        assert _deduplicate_results([]) == []


# ===================================================================
# _format_web_search_results
# ===================================================================

class TestFormatWebSearchResults:
    def test_uses_summary_over_snippet(self):
        """应优先使用 summary 字段。"""
        results = [
            {
                "title": "Title",
                "hostname": "example.com",
                "summary": "This is summary.",
                "snippet": "This is snippet.",
                "link": "http://example.com",
            }
        ]
        formatted = _format_web_search_results(results)
        assert "This is summary." in formatted
        assert "This is snippet." not in formatted
        assert "【搜索结果】 Title" in formatted
        assert "来源：example.com" in formatted
        assert "链接：http://example.com" in formatted

    def test_fallback_to_snippet(self):
        """无 summary 时应 fallback 到 snippet。"""
        results = [
            {
                "title": "Title",
                "hostname": "example.com",
                "summary": "",
                "snippet": "This is snippet.",
                "link": "http://example.com",
            }
        ]
        formatted = _format_web_search_results(results)
        assert "This is snippet." in formatted

    def test_empty_results(self):
        """空结果应返回提示文本。"""
        assert _format_web_search_results([]) == "未找到相关网络搜索结果。"

    def test_multiple_results(self):
        """多条结果应以双换行分隔。"""
        results = [
            {"title": "A", "summary": "s1", "link": "http://a.com"},
            {"title": "B", "summary": "s2", "link": "http://b.com"},
        ]
        formatted = _format_web_search_results(results)
        assert "【搜索结果】 A" in formatted
        assert "【搜索结果】 B" in formatted
        assert "\n\n" in formatted


# ===================================================================
# search_web (integration)
# ===================================================================

class TestSearchWebIntegration:
    @pytest.mark.asyncio
    async def test_parallel_search_merge_dedup_format(self):
        """端到端：扩展为 3 query → 并行搜索 → 合并 → 去重 → 格式化。"""
        q1_results = [
            {
                "title": "Python 入门教程",
                "hostname": "a.com",
                "summary": "从零开始学习 Python 编程基础知识与语法。",
                "link": "http://a.com",
                "rerankScore": 0.9,
            },
            {
                "title": "Python 性能优化指南",
                "hostname": "b.com",
                "summary": "提升 Python 代码运行效率的实用技巧与最佳实践。",
                "link": "http://b.com",
                "rerankScore": 0.8,
            },
        ]
        q2_results = [
            {
                "title": "Python 入门教程",
                "hostname": "a.com",
                "summary": "从零开始学习 Python 编程基础知识与语法。",
                "link": "http://a.com",
                "rerankScore": 0.85,
            },
            {
                "title": "Python Web 框架对比",
                "hostname": "c.com",
                "summary": "Django、Flask、FastAPI 三大框架的优缺点全面分析。",
                "link": "http://c.com",
                "rerankScore": 0.7,
            },
        ]

        async def _mock_iqs_search(query: str) -> list[dict]:
            if query == "q1":
                return q1_results
            return q2_results

        with patch(
            "app.graphs.nodes.toolnodes.web_search._expand_search_queries",
            return_value=["q1", "q2"],
        ), patch(
            "app.graphs.nodes.toolnodes.web_search._iqs_search_single",
            new=_mock_iqs_search,
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ):
            result = await search_web.ainvoke({"query": "test"})

        # "Python 入门教程" 出现两次（URL 相同），去重后只剩一条
        # "Python 性能优化指南" 和 "Python Web 框架对比" 保留
        assert "【搜索结果】 Python 入门教程" in result
        assert "【搜索结果】 Python 性能优化指南" in result
        assert "【搜索结果】 Python Web 框架对比" in result
        # "Python 入门教程" 只应出现一次
        assert result.count("【搜索结果】 Python 入门教程") == 1

    @pytest.mark.asyncio
    async def test_fallback_when_expansion_fails(self):
        """small 模型扩展失败时应降级为单 query 搜索。"""
        with patch(
            "app.graphs.nodes.toolnodes.web_search._expand_search_queries",
            return_value=["original query"],
        ):
            with patch(
                "app.graphs.nodes.toolnodes.web_search._iqs_search_single",
                return_value=[
                    {
                        "title": "Single Result",
                        "hostname": "x.com",
                        "summary": "s",
                        "link": "http://x.com",
                    }
                ],
            ), patch(
                "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
                "fake_key",
            ):
                result = await search_web.ainvoke({"query": "original query"})

        assert "【搜索结果】 Single Result" in result

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """空 query 应返回提示。"""
        result = await search_web.ainvoke({"query": ""})
        assert result == "未提供有效的搜索关键词。"

    @pytest.mark.asyncio
    async def test_no_api_key(self):
        """未配置 API key 应返回服务不可用。"""
        with patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "",
        ):
            result = await search_web.ainvoke({"query": "test"})
            assert result == "联网搜索服务暂时不可用。"

    @pytest.mark.asyncio
    async def test_partial_failure_in_parallel_search(self):
        """部分子 query 搜索失败时，应收集成功结果继续处理。"""

        async def _mock_iqs_search(query: str) -> list[dict]:
            if query == "q1":
                raise RuntimeError("fail")
            return [
                {
                    "title": "OK Result",
                    "hostname": "ok.com",
                    "summary": "ok",
                    "link": "http://ok.com",
                }
            ]

        with patch(
            "app.graphs.nodes.toolnodes.web_search._expand_search_queries",
            return_value=["q1", "q2"],
        ), patch(
            "app.graphs.nodes.toolnodes.web_search._iqs_search_single",
            new=_mock_iqs_search,
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ):
            result = await search_web.ainvoke({"query": "test"})

        assert "【搜索结果】 OK Result" in result

    @pytest.mark.asyncio
    async def test_records_full_web_search_flow_with_parallel_subqueries(self):
        """联网搜索应记录 query 扩展、并行子搜索和聚合 span。"""
        callback = AgentMonitoringCallback()
        graph_run_id = uuid.uuid4()
        await callback.on_chain_start(
            None,
            {"messages": []},
            run_id=graph_run_id,
            metadata={
                "user_id": 1,
                "conversation_id": 1,
                "input_message": "搜索 Python 新闻",
            },
        )
        trace_id = callback.trace_id
        assert trace_id is not None

        async def _mock_iqs_search(query: str) -> list[dict]:
            await asyncio.sleep(0.05)
            summary_by_query = {
                "q1": "Python release timeline and CPython runtime notes.",
                "q2": "Python data science ecosystem package updates.",
                "q3": "Python web framework deployment news.",
            }
            return [
                {
                    "title": f"Result {query}",
                    "hostname": "example.com",
                    "summary": summary_by_query[query],
                    "link": f"http://example.com/{query}",
                }
            ]

        with patch(
            "app.graphs.nodes.toolnodes.web_search._expand_search_queries",
            return_value=["q1", "q2", "q3"],
        ), patch(
            "app.graphs.nodes.toolnodes.web_search._iqs_search_single",
            new=_mock_iqs_search,
        ), patch(
            "app.graphs.nodes.toolnodes.web_search.settings.IQS_API_KEY",
            "fake_key",
        ):
            start = time.perf_counter()
            result = await search_web.ainvoke(
                {"query": "python"},
                config={
                    "callbacks": [callback],
                    "metadata": {"agent_trace_id": trace_id},
                },
            )
            elapsed = time.perf_counter() - start

        assert elapsed < 0.13
        assert "【搜索结果】 Result q1" in result

        buf = get_trace_buffer(trace_id)
        assert buf is not None
        web_spans = [s for s in buf["spans"] if s["span_type"] == "web_search"]
        assert {s["span_name"] for s in web_spans} >= {
            "query_expansion",
            "iqs_search_batch",
            "iqs_search_single",
            "result_aggregation",
        }

        expansion = next(s for s in web_spans if s["span_name"] == "query_expansion")
        assert expansion["output_data"]["queries"] == ["q1", "q2", "q3"]
        assert expansion["output_data"]["fallback"] is False

        batch = next(s for s in web_spans if s["span_name"] == "iqs_search_batch")
        assert batch["output_data"]["query_count"] == 3
        assert batch["output_data"]["parallel"] is True
        assert batch["output_data"]["failed_count"] == 0

        singles = [s for s in web_spans if s["span_name"] == "iqs_search_single"]
        assert len(singles) == 3
        assert {s["input_data"]["query"] for s in singles} == {"q1", "q2", "q3"}
        assert all(s["parent_tmp_span_id"] == batch["tmp_span_id"] for s in singles)

        aggregation = next(s for s in web_spans if s["span_name"] == "result_aggregation")
        assert aggregation["output_data"]["raw_count"] == 3
        assert aggregation["output_data"]["deduped_count"] == 3
