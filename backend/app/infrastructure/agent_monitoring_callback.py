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
from datetime import datetime, timezone
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import LLMResult

logger = logging.getLogger(__name__)

# 模块级缓冲：trace_id -> trace_data
# 在 graph 级 on_chain_end 时统一写入
_trace_buffers: dict[str, dict[str, Any]] = {}


class AgentMonitoringCallback(AsyncCallbackHandler):
    """Agent 监控 Callback。

    维护内存中的 trace/span 状态树，在 graph 执行结束时通过 service 异步持久化。
    所有方法均包裹 try/except，确保异常绝不抛到主流程。
    """

    def __init__(self) -> None:
        super().__init__()
        self.trace_id: str | None = None
        self._trace_started_at: float = 0.0

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

    def _safe_extract_usage(self, response: LLMResult) -> dict[str, int]:
        """从 LLMResult 中提取 token usage。"""
        try:
            if not response.generations:
                return {}
            first_gen = response.generations[0][0]
            message = getattr(first_gen, "message", None)
            if message is None:
                return {}
            usage = getattr(message, "usage_metadata", None) or {}
            return {
                "prompt_tokens": usage.get("input_tokens") or usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("output_tokens") or usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
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
                    "spans": [],
                    "error_type": None,
                    "error_message": None,
                    "metadata": {},
                }
                # 将 trace_id 写回 config metadata，供后续事件使用
                if "metadata" in kwargs and isinstance(kwargs["metadata"], dict):
                    kwargs["metadata"]["agent_trace_id"] = self.trace_id
                return

            # Node 级启动
            if trace_id and node_name and node_name not in ("__start__", "__end__"):
                buf = _trace_buffers.get(trace_id)
                if buf:
                    buf["node_steps"] += 1
                    buf["spans"].append({
                        "span_type": "node",
                        "span_name": node_name,
                        "status": "started",
                        "started_at": datetime.now(timezone.utc),
                        "latency_ms": None,
                        "input_data": None,
                        "output_data": None,
                        "error_info": None,
                        "token_usage": None,
                        "metadata": {},
                    })
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
                for span in reversed(buf.get("spans", [])):
                    if span["span_type"] == "node" and span["span_name"] == node_name and span.get("status") == "started":
                        span["status"] = "completed"
                        span["ended_at"] = datetime.now(timezone.utc)
                        if span.get("started_at"):
                            span["latency_ms"] = int(
                                (datetime.now(timezone.utc) - span["started_at"]).total_seconds() * 1000
                            )
                        break
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

            buf["spans"].append({
                "span_type": "llm",
                "span_name": model_name or "llm",
                "status": "started",
                "started_at": datetime.now(timezone.utc),
                "latency_ms": None,
                "input_data": {"prompts_count": len(prompts)},
                "output_data": None,
                "error_info": None,
                "token_usage": None,
                "metadata": {"model_name": model_name},
            })
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

            # 更新最后一个未完成的 llm span
            for span in reversed(buf.get("spans", [])):
                if span["span_type"] == "llm" and span.get("status") == "started":
                    span["status"] = "completed"
                    span["ended_at"] = datetime.now(timezone.utc)
                    if span.get("started_at"):
                        span["latency_ms"] = int(
                            (datetime.now(timezone.utc) - span["started_at"]).total_seconds() * 1000
                        )
                    span["token_usage"] = usage
                    # 尝试提取生成文本摘要
                    try:
                        if response.generations and response.generations[0]:
                            gen = response.generations[0][0]
                            msg = getattr(gen, "message", None)
                            if msg:
                                text = getattr(msg, "content", "")
                                if isinstance(text, str):
                                    span["output_data"] = {"content_preview": self._safe_truncate(text, 200)}
                    except Exception:
                        pass
                    break
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

            buf["spans"].append({
                "span_type": "tool",
                "span_name": tool_name,
                "status": "started",
                "started_at": datetime.now(timezone.utc),
                "latency_ms": None,
                "input_data": {"args": self._safe_truncate(input_str, 500)},
                "output_data": None,
                "error_info": None,
                "token_usage": None,
                "metadata": {},
            })
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
            for span in reversed(buf.get("spans", [])):
                if span["span_type"] == "tool" and span.get("status") == "started":
                    span["status"] = "completed"
                    span["ended_at"] = datetime.now(timezone.utc)
                    if span.get("started_at"):
                        span["latency_ms"] = int(
                            (datetime.now(timezone.utc) - span["started_at"]).total_seconds() * 1000
                        )
                    span["output_data"] = {"result_preview": self._safe_truncate(output_str, 500)}
                    break
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
