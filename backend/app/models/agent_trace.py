from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    desc,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentTrace(Base):
    """Agent 调用追踪顶层记录。

    一次完整的 Agent 调用（一次用户消息 → AI 回复）对应一条 trace。
    """

    __tablename__ = "agent_traces"

    __table_args__ = (
        Index(
            "idx_agent_traces_conv_started",
            "conversation_id",
            desc("started_at"),
        ),
        Index(
            "idx_agent_traces_user_started",
            "user_id",
            desc("started_at"),
        ),
        Index("idx_agent_traces_status", "status"),
        Index("idx_agent_traces_flagged", "is_flagged"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    graph_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="chat_agent"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tool_calls_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    node_steps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_flagged: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    meta: Mapped[dict | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
