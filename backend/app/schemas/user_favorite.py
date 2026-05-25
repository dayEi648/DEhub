from pydantic import BaseModel, ConfigDict

from app.schemas.blog_post import BlogPostListItem
from app.schemas.forum_zone import ForumZoneResponse
from app.schemas.forum_post import ForumPostResponse


class FavoriteStatusResponse(BaseModel):
    """收藏/关注状态响应"""
    is_favorited: bool

    model_config = ConfigDict(from_attributes=True)


class FollowStatusResponse(BaseModel):
    """关注状态响应"""
    is_followed: bool

    model_config = ConfigDict(from_attributes=True)


# ---------- 博客文章收藏 ----------

class BlogPostFavoriteListResponse(BaseModel):
    """博客文章收藏列表响应"""
    items: list[BlogPostListItem]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ---------- 分区关注 ----------

class ZoneFollowListResponse(BaseModel):
    """分区关注列表响应"""
    items: list[ForumZoneResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ---------- 论坛帖子收藏 ----------

class PostFavoriteListResponse(BaseModel):
    """论坛帖子收藏列表响应"""
    items: list[ForumPostResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
