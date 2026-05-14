import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
)
from app.services.chat_graph_service import ChatGraphService
from app.services.user_memory_service import delete_conversation_memories_task

router = APIRouter(prefix="/chat", tags=["AI对话"])

logger = logging.getLogger(__name__)


@router.post("/stream")
async def stream_chat(
    chat_in: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    流式对话（SSE）。

    - 传入 conversation_id 继续已有对话，留空则自动创建新对话
    - 返回 text/event-stream，每段 data 为 LLM 生成的文本增量
    - 最后以 `data: [DONE]\n\n` 标记结束
    """
    service = ChatGraphService(db)

    # 若指定了已有对话，先校验存在性与权限，避免在 SSE 流中抛 HTTPException
    if chat_in.conversation_id is not None:
        await asyncio.to_thread(
            service.get_conversation_or_raise,
            chat_in.conversation_id,
            current_user.id,
        )

    async def _generate():
        try:
            async for chunk in service.stream_chat(
                user_id=current_user.id,
                conversation_id=chat_in.conversation_id,
                content=chat_in.content,
            ):
                # 解析内部 meta 标记，转换为 SSE meta 事件
                if chunk.startswith("__META__:"):
                    _, meta = chunk.split(":", 1)
                    key, value = meta.split("=", 1)
                    if key == "conversation_id":
                        yield f'event: meta\ndata: {{"conversation_id":{value}}}\n\n'
                    continue
                yield f"data: {chunk}\n\n"
        except Exception:
            # SSE headers 已发送，无法更改 HTTP 状态码；
            # 通过 error 事件通知客户端后正常结束流
            logger.exception("SSE 流处理异常")
            yield 'event: error\ndata: {"message": "服务异常"}\n\n'
            return
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationListResponse:
    """
    获取当前用户的对话列表（按最近时间倒序）。
    """
    service = ChatGraphService(db)
    items, total = await service.list_conversations(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return ConversationListResponse(items=items, total=total)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
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
    service = ChatGraphService(db)
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    软删除对话（仅对话所有者可用）。
    同时清理 Checkpointer 和长期记忆向量。
    """
    service = ChatGraphService(db)
    await service.delete_conversation(conversation_id, current_user.id)
    background_tasks.add_task(
        delete_conversation_memories_task, conversation_id
    )
    return None
