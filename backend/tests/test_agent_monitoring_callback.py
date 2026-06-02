"""AgentMonitoringCallback 单元测试。"""

import uuid
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from app.infrastructure.agent_monitoring_callback import (
    AgentMonitoringCallback,
    get_trace_buffer,
)


class TestSafeExtractUsage:
    """测试 _safe_extract_usage 方法。"""

    def setup_method(self):
        self.callback = AgentMonitoringCallback()

    def _make_llm_result(self, usage_metadata: dict | None, response_metadata: dict | None) -> LLMResult:
        """构造包含指定 metadata 的 LLMResult。"""
        message = AIMessage(
            content="test",
            usage_metadata=usage_metadata,
            response_metadata=response_metadata,
        )
        generation = ChatGeneration(message=message)
        return LLMResult(generations=[[generation]])

    def test_extracts_standard_fields(self):
        """标准 usage_metadata 字段提取。"""
        result = self.callback._safe_extract_usage(
            self._make_llm_result(
                usage_metadata={
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
                response_metadata={},
            )
        )
        assert result["prompt_tokens"] == 100
        assert result["completion_tokens"] == 50
        assert result["total_tokens"] == 150

    def test_extracts_deepseek_extended_fields(self):
        """DeepSeek 扩展字段（cache hit/miss、reasoning tokens）提取。"""
        result = self.callback._safe_extract_usage(
            self._make_llm_result(
                usage_metadata={
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
                response_metadata={
                    "token_usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 50,
                        "total_tokens": 150,
                        "prompt_cache_hit_tokens": 80,
                        "prompt_cache_miss_tokens": 20,
                        "completion_tokens_details": {
                            "reasoning_tokens": 30,
                        },
                    },
                },
            )
        )
        assert result["prompt_tokens"] == 100
        assert result["completion_tokens"] == 50
        assert result["total_tokens"] == 150
        assert result["prompt_cache_hit_tokens"] == 80
        assert result["prompt_cache_miss_tokens"] == 20
        assert result["reasoning_tokens"] == 30

    def test_response_metadata_takes_priority(self):
        """response_metadata.token_usage 优先于 usage_metadata。"""
        result = self.callback._safe_extract_usage(
            self._make_llm_result(
                usage_metadata={
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                },
                response_metadata={
                    "token_usage": {
                        "prompt_tokens": 1000,
                        "completion_tokens": 500,
                        "total_tokens": 1500,
                    },
                },
            )
        )
        assert result["prompt_tokens"] == 1000
        assert result["completion_tokens"] == 500
        assert result["total_tokens"] == 1500

    def test_fallback_when_response_metadata_missing(self):
        """无 response_metadata 时 fallback 到 usage_metadata。"""
        result = self.callback._safe_extract_usage(
            self._make_llm_result(
                usage_metadata={
                    "input_tokens": 42,
                    "output_tokens": 21,
                    "total_tokens": 63,
                },
                response_metadata={},
            )
        )
        assert result["prompt_tokens"] == 42
        assert result["completion_tokens"] == 21
        assert result["total_tokens"] == 63

    def test_returns_defaults_for_missing_fields(self):
        """缺失扩展字段时返回 0 默认值。"""
        result = self.callback._safe_extract_usage(
            self._make_llm_result(
                usage_metadata={
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                },
                response_metadata={
                    "token_usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                },
            )
        )
        assert result["prompt_cache_hit_tokens"] == 0
        assert result["prompt_cache_miss_tokens"] == 0
        assert result["reasoning_tokens"] == 0

    def test_returns_empty_on_exception(self):
        """解析异常时返回空字典，不抛异常。"""
        result = self.callback._safe_extract_usage(
            LLMResult(generations=[])
        )
        assert result == {}


class TestSpanRunMatching:
    """测试 span 使用 run_id 精确匹配，支持嵌套与乱序结束。"""

    def setup_method(self):
        self.callback = AgentMonitoringCallback()

    async def _start_trace(self):
        run_id = uuid.uuid4()
        await self.callback.on_chain_start(
            None,
            {"messages": []},
            run_id=run_id,
            metadata={
                "user_id": 1,
                "conversation_id": 2,
                "input_message": "搜索 Python 新闻",
            },
        )
        assert self.callback.trace_id is not None
        return run_id, self.callback.trace_id

    @staticmethod
    def _make_llm_result(content: str) -> LLMResult:
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return LLMResult(generations=[[generation]])

    @pytest.mark.asyncio
    async def test_nested_spans_record_parent_tmp_id(self):
        graph_run_id, trace_id = await self._start_trace()
        node_run_id = uuid.uuid4()
        tool_run_id = uuid.uuid4()
        llm_run_id = uuid.uuid4()

        await self.callback.on_chain_start(
            None,
            {},
            run_id=node_run_id,
            parent_run_id=graph_run_id,
            metadata={"agent_trace_id": trace_id, "langgraph_node": "tool_executor"},
        )
        await self.callback.on_tool_start(
            {"name": "search_web"},
            '{"query":"python"}',
            run_id=tool_run_id,
            parent_run_id=node_run_id,
            metadata={"agent_trace_id": trace_id},
        )
        await self.callback.on_llm_start(
            {"kwargs": {"model": "small-model"}},
            ["prompt"],
            run_id=llm_run_id,
            parent_run_id=tool_run_id,
            metadata={"agent_trace_id": trace_id},
        )

        buf = get_trace_buffer(trace_id)
        assert buf is not None
        node_span = next(s for s in buf["spans"] if s["span_type"] == "node")
        tool_span = next(s for s in buf["spans"] if s["span_type"] == "tool")
        llm_span = next(s for s in buf["spans"] if s["span_type"] == "llm")

        assert tool_span["parent_tmp_span_id"] == node_span["tmp_span_id"]
        assert llm_span["parent_tmp_span_id"] == tool_span["tmp_span_id"]

    @pytest.mark.asyncio
    async def test_parallel_llm_end_updates_matching_run_only(self):
        _, trace_id = await self._start_trace()
        first_run_id = uuid.uuid4()
        second_run_id = uuid.uuid4()

        await self.callback.on_llm_start(
            {"kwargs": {"model": "first-model"}},
            ["first"],
            run_id=first_run_id,
            metadata={"agent_trace_id": trace_id},
        )
        await self.callback.on_llm_start(
            {"kwargs": {"model": "second-model"}},
            ["second"],
            run_id=second_run_id,
            metadata={"agent_trace_id": trace_id},
        )

        first_result = self._make_llm_result("first done")
        await self.callback.on_llm_end(
            first_result,
            run_id=first_run_id,
            metadata={"agent_trace_id": trace_id},
        )

        buf = get_trace_buffer(trace_id)
        assert buf is not None
        first_span = next(s for s in buf["spans"] if s["metadata"]["model_name"] == "first-model")
        second_span = next(s for s in buf["spans"] if s["metadata"]["model_name"] == "second-model")

        assert first_span["status"] == "completed"
        assert first_span["output_data"]["content_preview"] == "first done"
        assert second_span["status"] == "started"
