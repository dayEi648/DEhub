from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.blog_category import BlogCategoryBrief
from app.schemas.user import UserBriefInfo


class BlogPostBase(BaseModel):
    """博客文章基础字段"""
    title: str = Field(min_length=1, max_length=64)
    slug: str = Field(min_length=1, max_length=255)
    summary: Optional[str] = None
    content_md: str
    category_id: int = Field(ge=1)
    tags: list[str] = Field(default_factory=list)
    status: str = Field(default="draft", pattern=r"^(draft|published)$")


class BlogPostCreate(BlogPostBase):
    """创建博客文章请求"""
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    # summary 继承自 BlogPostBase (Optional[str])，服务层会强制设为 None
    status: str = Field(default="draft", pattern=r"^(draft)$")  # 强制草稿


class BlogPostUpdate(BaseModel):
    """更新博客文章请求：全可选。不允许前端修改摘要和状态（发布请使用专用接口）。"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=64)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    summary: Optional[str] = None  # 后端内部使用，前端传入会被忽略
    content_md: Optional[str] = None
    category_id: Optional[int] = Field(default=None, ge=1)
    tags: Optional[list[str]] = None
    status: Optional[str] = Field(default=None, pattern=r"^(draft|published)$")  # 后端会忽略此字段


class BlogPostResponse(BlogPostBase):
    """博客文章完整响应"""
    id: int
    user_id: int
    view_count: int
    comment_count: int
    cover_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    category: BlogCategoryBrief
    author: UserBriefInfo

    model_config = ConfigDict(from_attributes=True)


class BlogPostListItem(BaseModel):
    """博客文章列表项（不包含正文，减少传输量）"""
    id: int
    user_id: int
    title: str
    slug: str
    summary: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: int
    category: BlogCategoryBrief
    tags: list[str]
    status: str
    view_count: int
    comment_count: int
    created_at: datetime
    updated_at: datetime
    author: UserBriefInfo

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



