from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentSpan(Base):
    """Agent 调用链路中的细粒度 Span。

    记录一次 Trace 内的各个阶段：LLM 调用、工具执行、节点执行、业务事件等。
    """

    __tablename__ = "agent_spans"

    __table_args__ = (
        Index("idx_agent_spans_trace", "trace_id"),
        Index("idx_agent_spans_type", "span_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agent_traces.trace_id", ondelete="CASCADE"), nullable=False
    )
    parent_span_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("agent_spans.id", ondelete="CASCADE"), nullable=True
    )
    span_type: Mapped[str] = mapped_column(String(20), nullable=False)
    span_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_data: Mapped[dict | None] = mapped_column(
        "input_data", JSONB, nullable=True
    )
    output_data: Mapped[dict | None] = mapped_column(
        "output_data", JSONB, nullable=True
    )
    error_info: Mapped[dict | None] = mapped_column(
        "error_info", JSONB, nullable=True
    )
    token_usage: Mapped[dict | None] = mapped_column(
        "token_usage", JSONB, nullable=True
    )
    meta: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
