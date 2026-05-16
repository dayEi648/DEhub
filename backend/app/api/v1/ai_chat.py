from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.chat import ConversationListResponse, MessageResponse
from app.services.chat_service import ChatService


router = APIRouter(prefix="/ai_chat", tags=["AI 对话"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_in: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    AI 对话。
    Args:
        chat_in: ChatRequest
        db: Session
        current_user: User

    Returns:
        ChatResponse
    """
    service = ChatService(db)
    return await service.chat(chat_in, current_user.id)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ConversationListResponse:
    """
    获取当前用户的对话列表（按最近时间倒序）。
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: Session
        current_user: User
    Returns:
        ConversationListResponse
    """
    service = ChatService(db)
    items, total = await service.list_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return ConversationListResponse(items=items, total=total)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    include_hidden: bool = Query(
        default=False,
        description="是否包含隐藏的中间消息（如 tool_calls 决策消息、ToolMessage）",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    """
    获取某对话的消息列表（按时间正序）。
    默认过滤掉 AI 流程中的中间隐藏消息，供前端展示使用。
    设置 include_hidden=true 可查看完整消息流（供管理监控）。
    """
    service = ChatService(db)
    messages = await service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        include_hidden=include_hidden,
    )
    return messages


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    软删除对话（仅对话所有者可用）。
    同时清理 Checkpointer 中的对话历史。
    """
    service = ChatService(db)
    await service.delete_conversation(conversation_id, current_user.id)
    return None
