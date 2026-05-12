from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.forum_reply import (
    ForumReplyCreate,
    ForumReplyResponse,
    ForumReplyContent,
    ForumReplyListResponse,
)
from app.services.forum_reply_service import ForumReplyService

router = APIRouter(tags=["论坛回复管理"])


@router.post(
    "/forum_posts/{post_id}/replies",
    response_model=ForumReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reply(
    post_id: int,
    data: ForumReplyContent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumReplyResponse:
    """
    发表回复（登录用户）
    Args:
        post_id: 帖子ID
        data: 回复内容
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ForumReplyResponse: 回复响应
    """
    reply_in = ForumReplyCreate(post_id=post_id, content=data.content)
    service = ForumReplyService(db)
    return service.create_reply(post_id, reply_in, current_user)


@router.get("/forum_posts/{post_id}/replies", response_model=ForumReplyListResponse)
def list_replies(
    post_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumReplyListResponse:
    """
    查询某帖子下的回复列表（分页）
    Args:
        post_id: 帖子ID
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ForumReplyListResponse: 回复分页列表
    """
    service = ForumReplyService(db)
    items, total = service.list_replies_by_post(
        post_id=post_id, skip=skip, limit=limit
    )
    return ForumReplyListResponse(items=items, total=total)


@router.delete("/forum_replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除回复（作者本人 或 管理员 或 区主）
    Args:
        reply_id: 回复ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        None
    """
    service = ForumReplyService(db)
    service.delete_reply(reply_id, current_user)
    return None
