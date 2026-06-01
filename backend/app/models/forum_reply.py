from datetime import datetime
from sqlalchemy import DateTime, func, Integer, BigInteger, ForeignKey, Text, Index, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.forum_post import ForumPost
    from app.models.user import User


class ForumReply(Base):
    __tablename__ = "forum_replies"

    __table_args__ = (
        Index("idx_forum_replies_post_time", "post_id", desc("created_at")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("forum_posts.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    likecount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    post: Mapped["ForumPost"] = relationship("ForumPost", back_populates="replies")
