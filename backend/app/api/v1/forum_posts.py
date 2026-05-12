from typing import List
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.forum_post import (
    ForumPostCreate,
    ForumPostUpdate,
    ForumPostResponse,
)
from app.services.forum_post_service import ForumPostService

router = APIRouter(prefix="/forum_posts", tags=["论坛帖子管理"])


@router.post("/", response_model=ForumPostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    post_in: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostResponse:
    """
    发表帖子（登录用户）
    Args:
        post_in: 帖子创建请求
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ForumPostResponse: 帖子响应
    """
    service = ForumPostService(db)
    return service.create_post(post_in, current_user)


@router.get("/", response_model=List[ForumPostResponse])
def list_posts(
    zone_id: int | None = Query(default=None, ge=1),
    sort_by: str = Query(default="created", pattern=r"^(created|view)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ForumPostResponse]:
    """
    查询帖子列表（支持分区筛选、排序与分页）
    Args:
        zone_id: 分区ID筛选
        sort_by: 排序方式，"created" 按发布时间倒序，"view" 按浏览量倒序
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        List[ForumPostResponse]: 帖子列表
    """
    service = ForumPostService(db)
    return service.list_posts(
        zone_id=zone_id, sort_by=sort_by, skip=skip, limit=limit
    )


@router.get("/{post_id}", response_model=ForumPostResponse)
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostResponse:
    """
    根据 ID 查询帖子详情（同时增加浏览量）
    Args:
        post_id: 帖子ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ForumPostResponse: 帖子详情
    """
    service = ForumPostService(db)
    return service.get_post(post_id)


@router.put("/{post_id}", response_model=ForumPostResponse)
def update_post(
    post_id: int,
    post_in: ForumPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumPostResponse:
    """
    编辑帖子（作者本人 或 管理员及以上）
    Args:
        post_id: 帖子ID
        post_in: 帖子更新请求
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ForumPostResponse: 更新后的帖子详情
    """
    service = ForumPostService(db)
    return service.update_post(post_id, post_in, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除帖子（作者本人 或 管理员 或 区主）
    Args:
        post_id: 帖子ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        None
    """
    service = ForumPostService(db)
    service.delete_post(post_id, current_user)
    return None
