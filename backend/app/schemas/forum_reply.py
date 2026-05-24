from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserBriefInfo


class ForumReplyBase(BaseModel):
    """论坛回复基础字段"""
    post_id: int = Field(ge=1)
    content: str = Field(min_length=1)


class ForumReplyCreate(ForumReplyBase):
    """创建论坛回复请求"""
    pass


class ForumReplyResponse(ForumReplyBase):
    """论坛回复完整响应"""
    id: int
    user_id: int
    user: UserBriefInfo
    likecount: int
    comment_count: int
    created_at: datetime
    is_liked: bool = False

    model_config = ConfigDict(from_attributes=True)


class ForumReplyContent(BaseModel):
    """嵌套路由下仅需 content，post_id 来自路径参数"""
    content: str = Field(min_length=1)


class ForumReplyListResponse(BaseModel):
    """回复分页列表响应"""
    items: list[ForumReplyResponse]
    total: int
