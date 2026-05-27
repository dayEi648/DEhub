from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBriefInfo


class ForumPostBase(BaseModel):
    """论坛帖子基础字段"""
    title: str = Field(min_length=1, max_length=128)
    content: str = Field(min_length=1)
    zone_id: int = Field(ge=1)


class ForumPostCreate(ForumPostBase):
    """创建论坛帖子请求"""
    pass


class ForumPostUpdate(BaseModel):
    """更新论坛帖子请求：全可选"""
    title: str | None = Field(default=None, min_length=1, max_length=128)
    content: str | None = Field(default=None, min_length=1)
    zone_id: int | None = Field(default=None, ge=1)


class ForumPostResponse(ForumPostBase):
    """论坛帖子完整响应"""
    id: int
    user_id: int
    user: UserBriefInfo
    view_count: int
    reply_count: int
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumPostListItem(BaseModel):
    """论坛帖子列表项（轻量，不含完整 content）"""
    id: int
    title: str
    zone_id: int
    user_id: int
    user: UserBriefInfo
    view_count: int
    reply_count: int
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumPostListResponse(BaseModel):
    """论坛帖子分页列表响应"""
    items: list[ForumPostListItem]
    total: int

    model_config = ConfigDict(from_attributes=True)
