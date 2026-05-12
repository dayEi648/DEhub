from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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
    title: Optional[str] = Field(default=None, min_length=1, max_length=128)
    content: Optional[str] = Field(default=None, min_length=1)
    zone_id: Optional[int] = Field(default=None, ge=1)


class ForumPostResponse(ForumPostBase):
    """论坛帖子完整响应"""
    id: int
    user_id: int
    view_count: int
    reply_count: int
    updated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
