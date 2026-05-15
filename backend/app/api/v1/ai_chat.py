from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest, ChatResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.user import User
from app.core.security import get_current_user
import asyncio
from app.schemas.chat import ConversationListResponse, MessageResponse


router = APIRouter(prefix="/ai_chat", tags=["AI 对话"])

@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_in: ChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """
    AI 对话
    传入 conversation_id 继续已有对话，留空则自动创建新对话
    Args:
        chat_request: ChatRequest
        db: Session
        current_user: User
    Returns:
        ChatResponse
    """
    service = ChatService(db)

    # 若指定了已有对话，先校验存在性与权限
    if chat_in.conversation_id is not None:
        conv = await asyncio.to_thread(
            service.get_conversation_or_raise,
            chat_in.conversation_id,
            current_user.id,
        )
        if conv is None:
            raise HTTPException(status_code=404, detail="对话不存在或已删除")

    try:
        return await asyncio.to_thread(
            service.chat, 
            chat_in, 
            current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageResponse]:
    """
    获取某对话的消息列表（按时间正序）。
    """
    service = ChatService(db)
    messages = await service.get_messages(
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
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
