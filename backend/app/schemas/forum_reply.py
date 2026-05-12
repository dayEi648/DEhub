from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


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
    likecount: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ForumReplyContent(BaseModel):
    """嵌套路由下仅需 content，post_id 来自路径参数"""
    content: str = Field(min_length=1)


class ForumReplyListResponse(BaseModel):
    """回复分页列表响应"""
    items: list[ForumReplyResponse]
    total: int
