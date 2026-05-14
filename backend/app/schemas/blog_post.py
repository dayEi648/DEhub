from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.blog_category import BlogCategoryBrief


class BlogPostBase(BaseModel):
    """博客文章基础字段"""
    title: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=255)
    summary: Optional[str] = None
    content_md: str
    cover_image_url: Optional[str] = None
    category_id: int = Field(ge=1)
    tags: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern=r"^(draft|published)$")


class BlogPostCreate(BlogPostBase):
    """创建博客文章请求"""
    slug: str | None = Field(default=None, min_length=1, max_length=255)


class BlogPostUpdate(BaseModel):
    """更新博客文章请求：全可选"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=64)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    summary: Optional[str] = None
    content_md: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[int] = Field(default=None, ge=1)
    tags: Optional[list[str]] = None
    status: Optional[str] = Field(default=None, pattern=r"^(draft|published)$")


class BlogPostResponse(BlogPostBase):
    """博客文章完整响应"""
    id: int
    view_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    category: BlogCategoryBrief

    model_config = ConfigDict(from_attributes=True)


class BlogPostListItem(BaseModel):
    """博客文章列表项（不包含正文，减少传输量）"""
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: int
    category: BlogCategoryBrief
    tags: list[str]
    status: str
    view_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogPostListResponse(BaseModel):
    """博客文章列表分页响应"""
    items: list[BlogPostListItem]
    total: int

    model_config = ConfigDict(from_attributes=True)


class BlogPostDetailResponse(BlogPostResponse):
    """博客文章详情响应（包含相邻文章）"""
    prev_post: Optional[BlogPostListItem] = None
    next_post: Optional[BlogPostListItem] = None
