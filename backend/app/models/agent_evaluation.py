from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentEvaluation(Base):
    """Agent 输出质量评估记录。

    使用 LLM-as-Judge 或规则对单次 Agent 调用进行多维度评分。
    """

    __tablename__ = "agent_evaluations"

    __table_args__ = (
        Index("idx_agent_evaluations_trace", "trace_id"),
        Index("idx_agent_evaluations_dimension", "dimension", "score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("agent_traces.trace_id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    eval_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="auto_llm_judge"
    )
    dimension: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # relevance / helpfulness / tool_accuracy / coherence / latency
    score: Mapped[float] = mapped_column(
        Numeric(3, 2), nullable=False
    )  # 0.00 ~ 1.00
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    evaluator_model: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    meta: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
