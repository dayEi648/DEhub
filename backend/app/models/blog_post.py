from datetime import datetime
from sqlalchemy import String, DateTime, func, BigInteger, ARRAY, Integer, ForeignKey, CheckConstraint, Index, desc, text
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

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'published')", name="ck_blog_posts_status"),
        Index("idx_blog_posts_tags", "tags", postgresql_using="gin"),
        Index("idx_blog_posts_created_at", desc("created_at")),
        Index("idx_blog_posts_category_id", "category_id"),
        Index("idx_blog_posts_published_created_at", desc("created_at"), postgresql_where=text("status = 'published'")),
    )

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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    embedding: Mapped["BlogPostEmbedding | None"] = relationship(
        "BlogPostEmbedding", back_populates="post", uselist=False
    )

    @property
    def author(self):
        """兼容 schema 中的 author 字段，映射到 user 关系"""
        return self.user