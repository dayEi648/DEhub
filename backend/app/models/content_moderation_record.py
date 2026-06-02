from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    desc,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ContentModerationRecord(Base):
    """内容审核记录。

    记录每一次 AI Agent 对文本内容的审核过程与结果，
    包含审核输入快照、模型结论、处置计划与执行结果。
    """

    __tablename__ = "content_moderation_records"

    __table_args__ = (
        Index(
            "idx_cm_records_target",
            "target_type",
            "target_id",
            desc("created_at"),
        ),
        Index("idx_cm_records_status", "status", desc("created_at")),
        Index("idx_cm_records_trace", "trace_id"),
        Index("idx_cm_records_task", "task_id", unique=True),
        UniqueConstraint(
            "target_type", "target_id", "target_version",
            name="uq_cm_record_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    trace_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("agent_traces.trace_id", ondelete="SET NULL"),
        nullable=True,
    )
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    target_version: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_action: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none"
    )
    categories: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    original_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    moderation_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_plan: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
