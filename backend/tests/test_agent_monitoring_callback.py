"""AgentMonitoringCallback 单元测试。"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from app.infrastructure.agent_monitoring_callback import AgentMonitoringCallback


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
