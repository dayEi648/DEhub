from datetime import datetime
from sqlalchemy import String, DateTime, func, BigInteger, ARRAY, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.blog_category import BlogCategory
    from app.models.blog_post_embedding import BlogPostEmbedding
    from app.models.user import User


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(TEXT)
    content_md: Mapped[str] = mapped_column(TEXT, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(255))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", backref="blog_posts")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("blog_categories.id"), nullable=False)
    category: Mapped["BlogCategory"] = relationship("BlogCategory", back_populates="posts")
    tags: Mapped[list[str]] = mapped_column(ARRAY(TEXT), default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    embedding: Mapped["BlogPostEmbedding | None"] = relationship(
        "BlogPostEmbedding", back_populates="post", uselist=False
    )

    @property
    def author(self):
        """兼容 schema 中的 author 字段，映射到 user 关系"""
        return self.user