from pydantic import BaseModel, Field
from datetime import datetime


class _BaseChatSchema(BaseModel):
    """Schema 公共配置"""
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    """AI对话入参"""
    conversation_id: int | None = Field(default=None, description="对话ID，留空则创建新对话")
    user_input: str = Field(..., min_length=1, max_length=2000, description="用户输入")
    skip_side_effects: bool = Field(default=False, description="跳过标题生成与画像更新等副作用")
    is_edit: bool = Field(default=False, description="（已废弃）请使用 skip_side_effects")


class ChatResponse(BaseModel):
    """AI对话出参"""
    response: str = Field(..., description="AI对话响应")
    conversation_id: int = Field(..., description="对话ID")


class ConversationItem(_BaseChatSchema):
    """对话列表单项"""
    id: int = Field(..., description="对话ID")
    title: str = Field(..., description="对话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_message_at: datetime | None = Field(None, description="最后消息时间")


class ConversationListResponse(BaseModel):
    """对话列表出参"""
    items: list[ConversationItem] = Field(..., description="对话列表")
    total: int = Field(..., description="总对话数")


class MessageResponse(_BaseChatSchema):
    """对话消息出参"""
    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    meta: dict | None = Field(None, description="消息元数据（工具调用等）")
    created_at: datetime = Field(..., description="创建时间")
