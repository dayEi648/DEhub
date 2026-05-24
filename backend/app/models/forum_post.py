from datetime import datetime
from sqlalchemy import String, DateTime, func, BigInteger, Integer, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.forum_zone import ForumZone
    from app.models.forum_reply import ForumReply
    from app.models.user import User


class ForumPost(Base):
    __tablename__ = "forum_posts"

    __table_args__ = (
        CheckConstraint("reply_count >= 0", name="chk_posts_reply_count_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    zone_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("forum_zones.id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False
    )
    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reply_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User")
    zone: Mapped["ForumZone"] = relationship("ForumZone", back_populates="posts")
    replies: Mapped[list["ForumReply"]] = relationship(
        "ForumReply", back_populates="post", cascade="all, delete-orphan", passive_deletes=True
    )
