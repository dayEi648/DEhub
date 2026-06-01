from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, UniqueConstraint, Index, desc
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserPostFavorite(Base):
    __tablename__ = "user_post_favorites"

    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_user_post_favorites"),
        Index("idx_upf_user", "user_id", desc("created_at")),
        Index("idx_upf_post", "post_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("forum_posts.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
