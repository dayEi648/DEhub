from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.user_comment_like import UserCommentLike
from app.schemas.comment import CommentCreate, CommentResponse, CommentListResponse
from app.services.comment_service import CommentService

router = APIRouter(prefix="/comments", tags=["评论管理"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentResponse:
    """
    新增评论（登录用户）
    Args:
        comment_in: 评论创建请求
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        CommentResponse: 评论响应
    """
    service = CommentService(db)
    return service.create_comment(comment_in, current_user)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除评论（评论作者或管理员）
    若删除博客表层评论，会自动级联删除其下所有里层回复与嵌套回复。
    Args:
        comment_id: 评论ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        None
    """
    service = CommentService(db)
    service.delete_comment(comment_id, current_user)
    return None


@router.get("/", response_model=CommentListResponse)
def list_comments(
    target_type: str = Query(..., min_length=1, max_length=32),
    target_id: int = Query(..., ge=1),
    parent_id: int | None = Query(default=None, ge=1),
    is_nested: bool | None = Query(default=None),
    nested_parent_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="time", pattern=r"^(time|hot)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentListResponse:
    """
    分页查询评论列表
    - sort_by=time: 按创建时间倒序
    - sort_by=hot: 按点赞数倒序
    - parent_id 筛选某父级下的评论
    - is_nested 筛选是否嵌套回复
    - nested_parent_id 筛选引用某里层/回复评论的嵌套回复
    Args:
        target_type: 目标类型
        target_id: 目标ID
        parent_id: 父级ID
        is_nested: 是否嵌套回复
        nested_parent_id: 嵌套父级ID
        sort_by: 排序方式，"time" 或 "hot"
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        CommentListResponse: 评论分页列表响应
    """
    service = CommentService(db)
    items, total = service.list_comments(
        target_type=target_type,
        target_id=target_id,
        parent_id=parent_id,
        is_nested=is_nested,
        nested_parent_id=nested_parent_id,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )

    # 批量查询当前用户对这些评论的点赞状态
    response_items: list[CommentResponse] = []
    if items and current_user:
        comment_ids = [c.id for c in items]
        liked_rows = (
            db.query(UserCommentLike.comment_id)
            .filter(
                UserCommentLike.user_id == current_user.id,
                UserCommentLike.comment_id.in_(comment_ids),
            )
            .all()
        )
        liked_ids = {row[0] for row in liked_rows}
        for item in items:
            resp = CommentResponse.model_validate(item)
            resp.is_liked = item.id in liked_ids
            response_items.append(resp)
    else:
        response_items = [CommentResponse.model_validate(item) for item in items]

    return CommentListResponse(items=response_items, total=total)


@router.post("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    点赞评论（登录用户）
    Args:
        comment_id: 评论ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        None
    """
    service = CommentService(db)
    service.like_comment(comment_id, current_user)
    return None


@router.delete("/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    取消点赞评论（登录用户）
    Args:
        comment_id: 评论ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        None
    """
    service = CommentService(db)
    service.unlike_comment(comment_id, current_user)
    return None
