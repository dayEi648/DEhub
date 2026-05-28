"""
Pydantic 请求/响应模型定义。
"""
from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求体。"""

    session_id: Optional[str] = Field(default=None, description="会话ID，为空则自动创建新会话")
    message: str = Field(..., description="用户消息内容")


class ChatResponse(BaseModel):
    """对话响应体。"""

    reply: str
    session_id: str


class SessionCreateRequest(BaseModel):
    """创建会话请求体。"""

    title: Optional[str] = Field(default=None, description="会话标题，为空则自动生成")


# ========== 知识库相关模型 ==========


class KbSearchRequest(BaseModel):
    """知识库向量检索请求体。"""

    query: str = Field(..., description="检索查询文本", min_length=1)
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")


class KbSearchResponseItem(BaseModel):
    """知识库单条检索结果。"""

    doc_id: str
    title: Optional[str]
    content: str
    similarity: float
    metadata: dict


class KbUploadResponse(BaseModel):
    """知识库上传响应。"""

    doc_id: str
    title: str
    total_chunks: int
    message: str
