from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user_favorite import (
    FavoriteStatusResponse,
    FollowStatusResponse,
    BlogPostFavoriteListResponse,
    ZoneFollowListResponse,
    PostFavoriteListResponse,
)
from app.services.user_favorite_service import UserFavoriteService

router_favorites = APIRouter(prefix="/favorites", tags=["收藏管理"])
router_follows = APIRouter(prefix="/follows", tags=["关注管理"])


# ---------- 博客文章收藏 ----------

@router_favorites.post(
    "/blog-posts/{post_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def favorite_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    收藏博客文章（登录用户）
    Args:
        post_id: 文章ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    service.favorite_blog_post(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=True)


@router_favorites.delete(
    "/blog-posts/{post_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_200_OK,
)
def unfavorite_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    取消收藏博客文章（登录用户）
    Args:
        post_id: 文章ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    service.unfavorite_blog_post(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=False)


@router_favorites.get(
    "/blog-posts/{post_id}",
    response_model=FavoriteStatusResponse,
)
def get_blog_post_favorite_status(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    查询当前用户是否收藏了指定博客文章（登录用户）
    Args:
        post_id: 文章ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    is_favorited = service.is_blog_post_favorited(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=is_favorited)


@router_favorites.get(
    "/blog-posts",
    response_model=BlogPostFavoriteListResponse,
)
def list_blog_post_favorites(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BlogPostFavoriteListResponse:
    """
    获取当前用户的博客文章收藏列表（分页）
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        BlogPostFavoriteListResponse: 收藏列表
    """
    service = UserFavoriteService(db)
    return service.list_blog_post_favorites(skip, limit, current_user)


# ---------- 分区关注 ----------

@router_follows.post(
    "/zones/{zone_id}",
    response_model=FollowStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def follow_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowStatusResponse:
    """
    关注分区（登录用户）
    Args:
        zone_id: 分区ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FollowStatusResponse: 关注状态
    """
    service = UserFavoriteService(db)
    service.follow_zone(zone_id, current_user)
    return FollowStatusResponse(is_followed=True)


@router_follows.delete(
    "/zones/{zone_id}",
    response_model=FollowStatusResponse,
    status_code=status.HTTP_200_OK,
)
def unfollow_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowStatusResponse:
    """
    取消关注分区（登录用户）
    Args:
        zone_id: 分区ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FollowStatusResponse: 关注状态
    """
    service = UserFavoriteService(db)
    service.unfollow_zone(zone_id, current_user)
    return FollowStatusResponse(is_followed=False)


@router_follows.get(
    "/zones",
    response_model=ZoneFollowListResponse,
)
def list_zone_follows(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ZoneFollowListResponse:
    """
    获取当前用户的分区关注列表（分页）
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        ZoneFollowListResponse: 关注列表
    """
    service = UserFavoriteService(db)
    return service.list_zone_follows(skip, limit, current_user)


# ---------- 论坛帖子收藏 ----------

@router_favorites.post(
    "/forum-posts/{post_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_201_CREATED,
)
def favorite_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    收藏论坛帖子（登录用户）
    Args:
        post_id: 帖子ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    service.favorite_post(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=True)


@router_favorites.delete(
    "/forum-posts/{post_id}",
    response_model=FavoriteStatusResponse,
    status_code=status.HTTP_200_OK,
)
def unfavorite_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    取消收藏论坛帖子（登录用户）
    Args:
        post_id: 帖子ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    service.unfavorite_post(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=False)


@router_favorites.get(
    "/forum-posts/{post_id}",
    response_model=FavoriteStatusResponse,
)
def get_post_favorite_status(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FavoriteStatusResponse:
    """
    查询当前用户是否收藏了指定论坛帖子（登录用户）
    Args:
        post_id: 帖子ID
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        FavoriteStatusResponse: 收藏状态
    """
    service = UserFavoriteService(db)
    is_favorited = service.is_post_favorited(post_id, current_user)
    return FavoriteStatusResponse(is_favorited=is_favorited)


@router_favorites.get(
    "/forum-posts",
    response_model=PostFavoriteListResponse,
)
def list_post_favorites(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PostFavoriteListResponse:
    """
    获取当前用户的论坛帖子收藏列表（分页）
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
        current_user: 当前登录用户
    Returns:
        PostFavoriteListResponse: 收藏列表
    """
    service = UserFavoriteService(db)
    return service.list_post_favorites(skip, limit, current_user)
