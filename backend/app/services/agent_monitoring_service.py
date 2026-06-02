"""Agent 监控数据持久化服务。

负责将内存中的 trace/span 数据异步写入 PostgreSQL。
Phase 1 仅处理 agent_traces；Phase 2 扩展 agent_spans。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.crud import agent_trace as trace_crud
from app.crud import agent_span as span_crud
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


class AgentMonitoringService:
    """Agent 监控服务。

    所有写操作均在独立 Session 中执行，用于后台任务隔离。
    """

    @staticmethod
    async def persist_trace_async(buf: dict[str, Any]) -> None:
        """异步持久化一条 trace（含 spans）。

        Args:
            buf: AgentMonitoringCallback 构建的内存缓冲字典。
        """
        trace_id = buf.get("trace_id")
        if not trace_id:
            logger.warning("persist_trace_async 收到空 trace_id")
            return

        try:
            with SessionLocal() as db:
                # 检查是否已存在（防止重复写入）
                existing = trace_crud.get_agent_trace_by_trace_id(db, trace_id)
                # 将 DeepSeek 扩展 token 字段合并到 metadata
                metadata = buf.get("metadata") or {}
                for key in ("prompt_cache_hit_tokens", "prompt_cache_miss_tokens", "reasoning_tokens"):
                    if key in buf:
                        metadata[key] = buf[key]

                if existing:
                    trace = trace_crud.update_agent_trace(
                        db,
                        trace_id,
                        status=buf.get("status", "completed"),
                        output_message=buf.get("output_message"),
                        total_tokens=buf.get("total_tokens") or 0,
                        prompt_tokens=buf.get("prompt_tokens") or 0,
                        completion_tokens=buf.get("completion_tokens") or 0,
                        tool_calls_count=buf.get("tool_calls_count", 0),
                        node_steps=buf.get("node_steps", 0),
                        latency_ms=buf.get("latency_ms"),
                        ended_at=buf.get("ended_at"),
                        error_type=buf.get("error_type"),
                        error_message=buf.get("error_message"),
                        metadata=metadata,
                    )
                    logger.debug("更新已有 AgentTrace: %s", trace_id)
                else:
                    trace = trace_crud.create_agent_trace(
                        db,
                        trace_id=trace_id,
                        conversation_id=buf.get("conversation_id"),
                        user_id=buf.get("user_id"),
                        graph_name=buf.get("graph_name", "chat_agent"),
                        status=buf.get("status", "completed"),
                        input_message=buf.get("input_message"),
                        output_message=buf.get("output_message"),
                        total_tokens=buf.get("total_tokens") or 0,
                        prompt_tokens=buf.get("prompt_tokens") or 0,
                        completion_tokens=buf.get("completion_tokens") or 0,
                        tool_calls_count=buf.get("tool_calls_count", 0),
                        node_steps=buf.get("node_steps", 0),
                        latency_ms=buf.get("latency_ms"),
                        started_at=buf.get("started_at") or datetime.now(timezone.utc),
                        ended_at=buf.get("ended_at"),
                        error_type=buf.get("error_type"),
                        error_message=buf.get("error_message"),
                        metadata=metadata,
                    )
                    logger.debug("新建 AgentTrace: %s", trace_id)

                # Phase 2: 批量写入 agent_spans
                spans = buf.get("spans", [])
                if spans and trace:
                    try:
                        span_crud.batch_create_agent_spans(db, trace_id, spans)
                        logger.debug(
                            "批量写入 AgentSpans: trace=%s, spans=%d",
                            trace_id,
                            len(spans),
                        )
                    except Exception:
                        logger.exception(
                            "AgentSpans 批量写入失败: trace_id=%s", trace_id
                        )

                db.commit()
        except Exception:
            logger.exception("AgentTrace 持久化失败: trace_id=%s", trace_id)

    @staticmethod
    async def persist_span_async(
        trace_id: str,
        span_type: str,
        span_name: str,
        status: str = "completed",
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int | None = None,
        meta: dict | None = None,
    ) -> None:
        """异步直接写入单条 business span 到数据库。

        用于 trace 已持久化后追加的 span（如 compact、title、profile 等后台操作）。
        """
        try:
            with SessionLocal() as db:
                span_crud.batch_create_agent_spans(
                    db,
                    trace_id,
                    [
                        {
                            "span_type": span_type,
                            "span_name": span_name,
                            "status": status,
                            "started_at": datetime.now(timezone.utc),
                            "ended_at": datetime.now(timezone.utc),
                            "latency_ms": latency_ms,
                            "input_data": input_data,
                            "output_data": output_data,
                            "metadata": meta,
                        }
                    ],
                )
                db.commit()
                logger.debug(
                    "直接写入 business span: trace=%s, type=%s, name=%s",
                    trace_id,
                    span_type,
                    span_name,
                )
        except Exception:
            logger.exception("直接写入 business span 失败: trace_id=%s", trace_id)

    @staticmethod
    def record_business_span(
        trace_id: str,
        span_type: str,
        span_name: str,
        status: str = "completed",
        input_data: dict | None = None,
        output_data: dict | None = None,
        latency_ms: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """记录业务级 span（供 Callback 无法覆盖的手动埋点使用）。

        优先写入内存缓冲；若 trace 已弹出，则直接写入数据库。
        """
        from app.infrastructure.agent_monitoring_callback import get_trace_buffer

        buf = get_trace_buffer(trace_id)
        if not buf:
            logger.debug("record_business_span 找不到 trace 缓冲，跳过: %s", trace_id)
            return

        span = {
            "span_type": span_type,
            "span_name": span_name,
            "status": status,
            "started_at": datetime.now(timezone.utc),
            "ended_at": datetime.now(timezone.utc),
            "latency_ms": latency_ms,
            "input_data": input_data,
            "output_data": output_data,
            "metadata": metadata,
        }

        buf["spans"].append(span)
        logger.debug("记录业务 span: trace=%s, type=%s, name=%s", trace_id, span_type, span_name)

    @staticmethod
    def start_buffered_span(
        trace_id: str | None,
        span_type: str,
        span_name: str,
        input_data: dict | None = None,
        metadata: dict | None = None,
        parent_tmp_span_id: str | None = None,
    ) -> str | None:
        """在当前 trace 缓冲中启动业务 span，返回临时 span id。

        仅用于 graph 主 trace 尚未持久化时的细粒度内部步骤。
        """
        if not trace_id:
            return None

        from app.infrastructure.agent_monitoring_callback import (
            get_current_span_tmp_id,
            get_trace_buffer,
        )

        buf = get_trace_buffer(trace_id)
        if not buf:
            logger.debug("start_buffered_span 找不到 trace 缓冲，跳过: %s", trace_id)
            return None

        tmp_span_id = f"business-{uuid.uuid4().hex[:12]}"
        span = {
            "tmp_span_id": tmp_span_id,
            "parent_tmp_span_id": parent_tmp_span_id or get_current_span_tmp_id(),
            "span_type": span_type,
            "span_name": span_name,
            "status": "started",
            "started_at": datetime.now(timezone.utc),
            "ended_at": None,
            "latency_ms": None,
            "input_data": input_data,
            "output_data": None,
            "error_info": None,
            "token_usage": None,
            "metadata": metadata or {},
        }
        buf["spans"].append(span)
        return tmp_span_id

    @staticmethod
    def end_buffered_span(
        trace_id: str | None,
        tmp_span_id: str | None,
        status: str = "completed",
        output_data: dict | None = None,
        error_info: dict | None = None,
        metadata: dict | None = None,
    ) -> None:
        """结束缓冲中的业务 span。"""
        if not trace_id or not tmp_span_id:
            return

        from app.infrastructure.agent_monitoring_callback import get_trace_buffer

        buf = get_trace_buffer(trace_id)
        if not buf:
            return

        for span in reversed(buf.get("spans", [])):
            if span.get("tmp_span_id") == tmp_span_id:
                span["status"] = status
                span["ended_at"] = datetime.now(timezone.utc)
                if span.get("started_at"):
                    span["latency_ms"] = int(
                        (
                            datetime.now(timezone.utc) - span["started_at"]
                        ).total_seconds()
                        * 1000
                    )
                if output_data is not None:
                    span["output_data"] = output_data
                if error_info is not None:
                    span["error_info"] = error_info
                if metadata:
                    span["metadata"] = {**(span.get("metadata") or {}), **metadata}
                return
