"""Agent 行为监测 Callback。

通过 LangChain Core 的 AsyncCallbackHandler 注入 graph.ainvoke()，
在 LangGraph 1.2 中已验证可正确捕获 on_chain_start/end、on_llm_start/end、on_tool_start/end。

关键验证点：
- 节点名通过 kwargs['metadata']['langgraph_node'] 获取
- Callback 沿 config 自动传播到所有 Node、LLM、Tool 调用
- 无需为每个 Tool/Node 单独注入
"""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

# 模块级缓冲：trace_id -> trace_data
# 在 graph 级 on_chain_end 时统一写入
# 使用 OrderedDict + 容量上限，防止极端情况下内存无限增长
from collections import OrderedDict
_trace_buffers: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX_TRACE_BUFFER_SIZE = 1000

_current_trace_id_var: ContextVar[str | None] = ContextVar(
    "agent_monitoring_trace_id", default=None
)
_current_span_tmp_id_var: ContextVar[str | None] = ContextVar(
    "agent_monitoring_span_tmp_id", default=None
)


class AgentMonitoringCallback(AsyncCallbackHandler):
    """Agent 监控 Callback。

    维护内存中的 trace/span 状态树，在 graph 执行结束时通过 service 异步持久化。
    所有方法均包裹 try/except，确保异常绝不抛到主流程。
    """

    def __init__(self) -> None:
        super().__init__()
        self.trace_id: str | None = None
        self._trace_started_at: float = 0.0
        self._run_span_tmp_ids: dict[str, str] = {}

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _get_trace_id(self, kwargs: dict) -> str | None:
        """从 config metadata 中提取 trace_id。"""
        metadata = kwargs.get("metadata") or {}
        return metadata.get("agent_trace_id")

    def _get_node_name(self, kwargs: dict) -> str | None:
        """从 metadata 中提取 langgraph_node 名称。"""
        metadata = kwargs.get("metadata") or {}
        return metadata.get("langgraph_node")

    def _safe_extract_usage(self, response: LLMResult) -> dict[str, Any]:
        """从 LLMResult 中提取 token usage（含 DeepSeek 扩展字段）。"""
        try:
            if not response.generations:
                return {}
            first_gen = response.generations[0][0]
            message = getattr(first_gen, "message", None)
            if message is None:
                return {}

            # 优先从 response_metadata.token_usage 读取 DeepSeek 完整字段
            resp_meta = getattr(message, "response_metadata", None) or {}
            token_usage = resp_meta.get("token_usage") or {}
            completion_details = token_usage.get("completion_tokens_details") or {}

            # usage_metadata 作为 fallback 提供标准字段
            usage_meta = getattr(message, "usage_metadata", None) or {}

            return {
                "prompt_tokens": token_usage.get("prompt_tokens") or usage_meta.get("input_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens") or usage_meta.get("output_tokens", 0),
                "total_tokens": token_usage.get("total_tokens") or usage_meta.get("total_tokens", 0),
                "prompt_cache_hit_tokens": token_usage.get("prompt_cache_hit_tokens", 0),
                "prompt_cache_miss_tokens": token_usage.get("prompt_cache_miss_tokens", 0),
                "reasoning_tokens": completion_details.get("reasoning_tokens", 0),
            }
        except Exception:
            return {}

    def _safe_truncate(self, text: str | None, max_len: int = 500) -> str | None:
        """安全截断文本。"""
        if not text:
            return text
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def _make_tmp_span_id(self, span_type: str, run_id) -> str:
        return f"{span_type}-{str(run_id)}"

    def _resolve_parent_tmp_span_id(self, parent_run_id, kwargs: dict) -> str | None:
        metadata = kwargs.get("metadata") or {}
        explicit_parent = metadata.get("agent_parent_span_tmp_id")
        if explicit_parent:
            return explicit_parent
        if parent_run_id is not None:
            parent_tmp = self._run_span_tmp_ids.get(str(parent_run_id))
            if parent_tmp:
                return parent_tmp
        return None

    def _append_span(
        self,
        buf: dict[str, Any],
        *,
        run_id,
        parent_run_id=None,
        span_type: str,
        span_name: str,
        input_data: dict | None = None,
        metadata: dict | None = None,
        kwargs: dict | None = None,
    ) -> dict[str, Any]:
        tmp_span_id = self._make_tmp_span_id(span_type, run_id)
        parent_tmp_span_id = self._resolve_parent_tmp_span_id(
            parent_run_id, kwargs or {}
        )
        span = {
            "tmp_span_id": tmp_span_id,
            "parent_tmp_span_id": parent_tmp_span_id,
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
            "span_type": span_type,
            "span_name": span_name,
            "status": "started",
            "started_at": datetime.now(timezone.utc),
            "latency_ms": None,
            "input_data": input_data,
            "output_data": None,
            "error_info": None,
            "token_usage": None,
            "metadata": metadata or {},
        }
        self._run_span_tmp_ids[str(run_id)] = tmp_span_id
        buf["spans"].append(span)
        _current_trace_id_var.set(buf["trace_id"])
        _current_span_tmp_id_var.set(tmp_span_id)
        return span

    @staticmethod
    def _complete_span(
        span: dict[str, Any],
        *,
        output_data: dict | None = None,
        token_usage: dict | None = None,
    ) -> None:
        span["status"] = "completed"
        span["ended_at"] = datetime.now(timezone.utc)
        if span.get("started_at"):
            span["latency_ms"] = int(
                (datetime.now(timezone.utc) - span["started_at"]).total_seconds()
                * 1000
            )
        if output_data is not None:
            span["output_data"] = output_data
        if token_usage is not None:
            span["token_usage"] = token_usage

    @staticmethod
    def _find_span_by_run_id(buf: dict[str, Any], run_id) -> dict[str, Any] | None:
        run_id_text = str(run_id)
        for span in reversed(buf.get("spans", [])):
            if span.get("run_id") == run_id_text:
                return span
        return None

    # ------------------------------------------------------------------
    # on_chain_start / on_chain_end — Graph + Node 级别
    # ------------------------------------------------------------------

    async def on_chain_start(
        self, serialized: dict[str, Any] | None, inputs: dict[str, Any], *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            node_name = self._get_node_name(kwargs)
            trace_id = self._get_trace_id(kwargs)

            # Graph 级启动（name=unknown 或 None，且无 parent_run_id）
            if not parent_run_id and trace_id is None:
                self.trace_id = f"agent-{uuid.uuid4().hex[:12]}"
                self._trace_started_at = time.time()

                metadata = kwargs.get("metadata") or {}
                user_id = metadata.get("user_id")
                conversation_id = metadata.get("conversation_id")
                input_message = metadata.get("input_message")

                # 从 inputs 中提取用户输入（fallback）
                if not input_message and isinstance(inputs, dict):
                    messages = inputs.get("messages", [])
                    if messages and hasattr(messages[-1], "content"):
                        content = messages[-1].content
                        if isinstance(content, str):
                            input_message = content

                # 容量保护：超出上限时淘汰最旧的 trace
                if len(_trace_buffers) >= _MAX_TRACE_BUFFER_SIZE:
                    _trace_buffers.popitem(last=False)
                _trace_buffers[self.trace_id] = {
                    "trace_id": self.trace_id,
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "status": "started",
                    "input_message": self._safe_truncate(input_message, 500),
                    "started_at": datetime.now(timezone.utc),
                    "node_steps": 0,
                    "tool_calls_count": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "prompt_cache_hit_tokens": 0,
                    "prompt_cache_miss_tokens": 0,
                    "reasoning_tokens": 0,
                    "spans": [],
                    "error_type": None,
                    "error_message": None,
                    "metadata": {},
                }
                _current_trace_id_var.set(self.trace_id)
                _current_span_tmp_id_var.set(None)
                # 将 trace_id 写回 config metadata，供后续事件使用
                if "metadata" in kwargs and isinstance(kwargs["metadata"], dict):
                    kwargs["metadata"]["agent_trace_id"] = self.trace_id
                return

            # Node 级启动
            if trace_id and node_name and node_name not in ("__start__", "__end__"):
                buf = _trace_buffers.get(trace_id)
                if buf:
                    buf["node_steps"] += 1
                    self._append_span(
                        buf,
                        run_id=run_id,
                        parent_run_id=parent_run_id,
                        span_type="node",
                        span_name=node_name,
                        kwargs=kwargs,
                    )
        except Exception:
            logger.exception("AgentMonitoringCallback.on_chain_start 异常")

    async def on_chain_end(
        self, outputs: dict[str, Any], *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            node_name = self._get_node_name(kwargs)
            trace_id = self._get_trace_id(kwargs) or self.trace_id

            if not trace_id:
                return

            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            # Graph 级结束（无 parent_run_id）
            if not parent_run_id:
                ended_at = datetime.now(timezone.utc)
                latency_ms = int((time.time() - self._trace_started_at) * 1000) if self._trace_started_at else None

                # 从 outputs 提取最终消息
                messages = outputs.get("messages", []) if isinstance(outputs, dict) else []
                output_text = ""
                if messages and isinstance(messages, list):
                    last_msg = messages[-1]
                    if isinstance(last_msg, AIMessage):
                        content = last_msg.content
                        if isinstance(content, str):
                            output_text = content
                        elif isinstance(content, list):
                            output_text = "".join(
                                str(p.get("text", "")) if isinstance(p, dict) else str(p)
                                for p in content
                            )

                buf["status"] = "completed"
                buf["ended_at"] = ended_at
                buf["latency_ms"] = latency_ms
                buf["output_message"] = self._safe_truncate(output_text, 500)

                # 触发异步持久化
                self._persist_trace(trace_id)
                return

            # Node 级结束 — 更新对应 span
            if node_name:
                span = self._find_span_by_run_id(buf, run_id)
                if span and span["span_type"] == "node":
                    self._complete_span(span)
        except Exception:
            logger.exception("AgentMonitoringCallback.on_chain_end 异常")

    # ------------------------------------------------------------------
    # on_llm_start / on_llm_end — LLM 调用级别
    # ------------------------------------------------------------------

    async def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            trace_id = self._get_trace_id(kwargs) or self.trace_id
            if not trace_id:
                return
            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            model_name = ""
            if serialized and "kwargs" in serialized:
                model_name = serialized["kwargs"].get("model", "")

            self._append_span(
                buf,
                run_id=run_id,
                parent_run_id=parent_run_id,
                span_type="llm",
                span_name=model_name or "llm",
                input_data={"prompts_count": len(prompts)},
                metadata={"model_name": model_name},
                kwargs=kwargs,
            )
        except Exception:
            logger.exception("AgentMonitoringCallback.on_llm_start 异常")

    async def on_llm_end(
        self, response: LLMResult, *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            trace_id = self._get_trace_id(kwargs) or self.trace_id
            if not trace_id:
                return
            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            usage = self._safe_extract_usage(response)
            buf["total_tokens"] = (buf.get("total_tokens") or 0) + usage.get("total_tokens", 0)
            buf["prompt_tokens"] = (buf.get("prompt_tokens") or 0) + usage.get("prompt_tokens", 0)
            buf["completion_tokens"] = (buf.get("completion_tokens") or 0) + usage.get("completion_tokens", 0)
            buf["prompt_cache_hit_tokens"] = (buf.get("prompt_cache_hit_tokens") or 0) + usage.get("prompt_cache_hit_tokens", 0)
            buf["prompt_cache_miss_tokens"] = (buf.get("prompt_cache_miss_tokens") or 0) + usage.get("prompt_cache_miss_tokens", 0)
            buf["reasoning_tokens"] = (buf.get("reasoning_tokens") or 0) + usage.get("reasoning_tokens", 0)

            output_data = None
            try:
                if response.generations and response.generations[0]:
                    gen = response.generations[0][0]
                    msg = getattr(gen, "message", None)
                    if msg:
                        text = getattr(msg, "content", "")
                        if isinstance(text, str):
                            output_data = {
                                "content_preview": self._safe_truncate(text, 200)
                            }
            except Exception:
                pass

            span = self._find_span_by_run_id(buf, run_id)
            if span and span["span_type"] == "llm":
                self._complete_span(span, output_data=output_data, token_usage=usage)
        except Exception:
            logger.exception("AgentMonitoringCallback.on_llm_end 异常")

    # ------------------------------------------------------------------
    # on_tool_start / on_tool_end — Tool 调用级别
    # ------------------------------------------------------------------

    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            trace_id = self._get_trace_id(kwargs) or self.trace_id
            if not trace_id:
                return
            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            tool_name = serialized.get("name", "unknown") if serialized else "unknown"
            buf["tool_calls_count"] = buf.get("tool_calls_count", 0) + 1

            span = self._append_span(
                buf,
                run_id=run_id,
                parent_run_id=parent_run_id,
                span_type="tool",
                span_name=tool_name,
                input_data={"args": self._safe_truncate(input_str, 500)},
                kwargs=kwargs,
            )
            metadata = kwargs.get("metadata") or {}
            if isinstance(metadata, dict):
                metadata["agent_current_tool_tmp_span_id"] = span["tmp_span_id"]
        except Exception:
            logger.exception("AgentMonitoringCallback.on_tool_start 异常")

    async def on_tool_end(
        self, output: Any, *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            trace_id = self._get_trace_id(kwargs) or self.trace_id
            if not trace_id:
                return
            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            output_str = str(output) if output is not None else ""
            span = self._find_span_by_run_id(buf, run_id)
            if span and span["span_type"] == "tool":
                self._complete_span(
                    span,
                    output_data={
                        "result_preview": self._safe_truncate(output_str, 500)
                    },
                )
        except Exception:
            logger.exception("AgentMonitoringCallback.on_tool_end 异常")

    # ------------------------------------------------------------------
    # 错误处理
    # ------------------------------------------------------------------

    async def on_chain_error(
        self, error: BaseException, *, run_id, parent_run_id=None, **kwargs
    ) -> None:
        try:
            trace_id = self._get_trace_id(kwargs) or self.trace_id
            if not trace_id:
                return
            buf = _trace_buffers.get(trace_id)
            if not buf:
                return

            buf["status"] = "failed"
            buf["error_type"] = type(error).__name__
            buf["error_message"] = str(error)[:1000]

            if not parent_run_id:
                buf["ended_at"] = datetime.now(timezone.utc)
                latency_ms = int((time.time() - self._trace_started_at) * 1000) if self._trace_started_at else None
                buf["latency_ms"] = latency_ms
                self._persist_trace(trace_id)
        except Exception:
            logger.exception("AgentMonitoringCallback.on_chain_error 异常")

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------

    def _persist_trace(self, trace_id: str) -> None:
        """触发 trace 异步持久化。"""
        try:
            buf = _trace_buffers.pop(trace_id, None)
            if not buf:
                return

            # 延迟导入避免循环依赖
            from app.services.agent_monitoring_service import AgentMonitoringService

            # 使用后台任务异步写入
            from app.infrastructure.background_tasks import background_task_manager

            background_task_manager.create_task(
                AgentMonitoringService.persist_trace_async(buf),
                name=f"agent_monitoring.persist_trace.{trace_id}",
            )
        except Exception:
            logger.exception("AgentMonitoringCallback._persist_trace 失败: trace_id=%s", trace_id)


def get_trace_buffer(trace_id: str) -> dict[str, Any] | None:
    """获取指定 trace_id 的内存缓冲（供外部业务埋点使用）。"""
    return _trace_buffers.get(trace_id)


def get_current_trace_id() -> str | None:
    """获取当前 callback 上下文中的 trace_id。"""
    return _current_trace_id_var.get()


def get_current_span_tmp_id() -> str | None:
    """获取当前 callback 上下文中的 span 临时 ID。"""
    return _current_span_tmp_id_var.get()


def clear_trace_buffer(trace_id: str | None = None) -> None:
    """清理指定 trace_id 的内存缓冲，或清空全部缓冲。

    Args:
        trace_id: 为 None 时清空全部缓冲；否则仅移除该 trace_id。
    """
    if trace_id:
        _trace_buffers.pop(trace_id, None)
    else:
        _trace_buffers.clear()
