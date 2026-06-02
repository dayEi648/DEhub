from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CommentUserInfo(BaseModel):
    """评论中嵌套的精简用户信息"""
    id: int
    username: str
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    """创建评论请求"""
    target_type: str = Field(min_length=1, max_length=32)
    target_id: int = Field(ge=1)
    parent_id: int | None = Field(default=None, ge=1)
    is_nested: bool = Field(default=False)
    nested_parent_id: int | None = Field(default=None, ge=1)
    content: str = Field(min_length=1, max_length=50000)


class CommentResponse(BaseModel):
    """评论完整响应"""
    id: int
    target_type: str
    target_id: int
    parent_id: int | None = None
    user_id: int
    content: str
    is_nested: bool
    nested_parent_id: int | None = None
    likecount: int
    is_liked: bool = False
    created_at: datetime
    user: CommentUserInfo

    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    """评论分页列表响应"""
    items: list[CommentResponse]
    total: int
