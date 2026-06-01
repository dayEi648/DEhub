from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, UniqueConstraint, Index, desc
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserCommentLike(Base):
    __tablename__ = "user_comment_likes"

    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_user_comment_likes_user"),
        Index("idx_user_comment_likes_user", "user_id", desc("created_at")),
        Index("idx_user_comment_likes_created", desc("created_at")),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
