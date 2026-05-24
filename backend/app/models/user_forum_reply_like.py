from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserForumReplyLike(Base):
    __tablename__ = "user_forum_reply_likes"

    __table_args__ = (
        UniqueConstraint("reply_id", "user_id", name="uq_user_forum_reply_likes_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reply_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("forum_replies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
