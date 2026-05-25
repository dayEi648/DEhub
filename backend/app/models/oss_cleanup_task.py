from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OssCleanupTask(Base):
    __tablename__ = "oss_cleanup_tasks"

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'succeeded', 'failed')",
            name="ck_oss_cleanup_tasks_status",
        ),
        Index("idx_oss_cleanup_tasks_status_next_retry", "status", "next_retry_at"),
        Index("idx_oss_cleanup_tasks_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
