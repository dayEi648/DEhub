from datetime import datetime
from sqlalchemy import String, DateTime, func, ForeignKey, Text, Integer, Boolean, Index, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Comment(Base):
    __tablename__ = "comments"

    __table_args__ = (
        Index("idx_comments_target_time", "target_type", "target_id", desc("created_at")),
        Index("idx_comments_parent_nested", "parent_id", "is_nested", desc("created_at")),
        Index("idx_comments_target_likes", "target_type", "target_id", desc("likecount")),
        Index("idx_comments_created_at", desc("created_at")),
        Index("idx_comments_nested_parent_time", "nested_parent_id", desc("created_at")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_nested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nested_parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    likecount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
