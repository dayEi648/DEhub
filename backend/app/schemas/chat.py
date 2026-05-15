from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    """AI对话入参"""
    conversation_id: Optional[int] = Field(default=None, description="对话ID，留空则创建新对话")
    user_input: str = Field(..., min_length=1, description="用户输入")


class ChatResponse(BaseModel):
    """AI对话出参"""
    response: str = Field(..., description="AI对话响应")
    conversation_id: int = Field(..., description="对话ID")


class ConversationItem(BaseModel):
    """对话列表单项"""
    model_config = {"from_attributes": True}

    id: int = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ConversationListResponse(BaseModel):
    """对话列表出参"""
    items: list[ConversationItem] = Field(..., description="对话列表")
    total: int = Field(..., description="总对话数")


class MessageResponse(BaseModel):
    """对话消息出参"""
    model_config = {"from_attributes": True}

    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    created_at: datetime = Field(..., description="创建时间")
