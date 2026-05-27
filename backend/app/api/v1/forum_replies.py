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
    """发表回复（登录用户）。"""
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
    """查询某帖子下的回复列表（分页）。"""
    service = ForumReplyService(db)
    items, total = service.list_replies_by_post(
        post_id=post_id, skip=skip, limit=limit, current_user=current_user
    )
    return ForumReplyListResponse(items=items, total=total)


@router.delete("/forum_replies/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除回复（作者本人、管理员或区主）。"""
    service = ForumReplyService(db)
    service.delete_reply(reply_id, current_user)
    return None


@router.post("/forum_replies/{reply_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """点赞回复（登录用户）。"""
    service = ForumReplyService(db)
    service.like_reply(reply_id, current_user)
    return None


@router.delete("/forum_replies/{reply_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_reply(
    reply_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """取消点赞回复（登录用户）。"""
    service = ForumReplyService(db)
    service.unlike_reply(reply_id, current_user)
    return None
