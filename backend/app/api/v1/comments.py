from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["评论管理"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentResponse:
    """新增评论（登录用户）。"""
    service = CommentService(db)
    return service.create_comment(comment_in, current_user)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除评论（评论作者或管理员，删除表层评论会级联删除其下所有嵌套回复）。"""
    service = CommentService(db)
    service.delete_comment(comment_id, current_user)
    return None


@router.get("/", response_model=CommentListResponse)
def list_comments(
    target_type: str = Query(..., min_length=1, max_length=32),
    target_id: int = Query(..., ge=1),
    parent_id: int | None = Query(default=None, ge=0),
    is_nested: bool | None = Query(default=None),
    nested_parent_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="time", pattern=r"^(time|time_asc|hot)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentListResponse:
    """分页查询评论列表（支持排序、嵌套回复筛选）。"""
    service = CommentService(db)
    items, total = service.list_comments_with_like_state(
        target_type=target_type,
        target_id=target_id,
        parent_id=parent_id,
        is_nested=is_nested,
        nested_parent_id=nested_parent_id,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
        current_user=current_user,
    )
    return CommentListResponse(items=items, total=total)


@router.post("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """点赞评论（登录用户）。"""
    service = CommentService(db)
    service.like_comment(comment_id, current_user)
    return None


@router.delete("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """取消点赞评论（登录用户）。"""
    service = CommentService(db)
    service.unlike_comment(comment_id, current_user)
    return None
