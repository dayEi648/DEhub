from datetime import datetime
from sqlalchemy import DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class UserBlogPostFavorite(Base):
    __tablename__ = "user_blog_post_favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    blog_post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("blog_posts.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
