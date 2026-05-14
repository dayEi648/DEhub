from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    """流式对话请求"""
    conversation_id: Optional[int] = Field(
        default=None, ge=1, description="对话ID，留空则创建新对话"
    )
    content: str = Field(min_length=1, description="用户消息内容")


class ConversationResponse(BaseModel):
    """对话元数据响应"""
    id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """单条消息响应"""
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    """对话分页列表响应"""
    items: list[ConversationResponse]
    total: int
