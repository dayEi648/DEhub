from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer, UniqueConstraint, Index, desc
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserBlogPostFavorite(Base):
    __tablename__ = "user_blog_post_favorites"

    __table_args__ = (
        UniqueConstraint("user_id", "blog_post_id", name="uq_user_blog_post_favorites"),
        Index("idx_ubpf_user", "user_id", desc("created_at")),
        Index("idx_ubpf_blog_post", "blog_post_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    blog_post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blog_posts.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
