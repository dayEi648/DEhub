from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBriefInfo


class ForumZoneBase(BaseModel):
    """论坛分区基础字段"""
    slug: str = Field(min_length=1, max_length=255)
    zone_name: str = Field(min_length=1, max_length=64)
    description: Optional[str] = None


class ForumZoneCreate(ForumZoneBase):
    """创建论坛分区请求"""
    slug: str | None = Field(default=None, min_length=1, max_length=255)


class ForumZoneUpdate(BaseModel):
    """更新论坛分区请求：全可选"""
    slug: Optional[str] = Field(default=None, min_length=1, max_length=255)
    zone_name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    description: Optional[str] = None
    manager_id: Optional[int] = Field(default=None, ge=1)


class ForumZoneResponse(ForumZoneBase):
    """论坛分区完整响应"""
    id: int
    manager_id: int
    manager: UserBriefInfo
    view_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
