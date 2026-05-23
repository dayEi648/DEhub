from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.blog_post import BlogPost
from app.core.permission_levels import PermissionLevel
from app.crud import user_favorite as favorite_crud
from app.crud import blog_post as blog_post_crud
from app.crud import forum_zone as forum_zone_crud
from app.crud import forum_post as forum_post_crud
from app.schemas.user_favorite import (
    BlogPostFavoriteListResponse,
    ZoneFollowListResponse,
    PostFavoriteListResponse,
)
from app.schemas.blog_post import BlogPostListItem
from app.schemas.forum_zone import ForumZoneResponse
from app.schemas.forum_post import ForumPostResponse


class UserFavoriteService:
    def __init__(self, db: Session):
        """
        初始化 UserFavoriteService
        Args:
            db: 数据库会话
        """
        self.db = db

    # ---------- 博客文章收藏 ----------

    def _get_visible_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        """
        获取当前用户可见的单篇博客文章
        Args:
            post_id: 文章ID
            current_user: 当前登录用户
        Returns:
            BlogPost | None: 文章对象或None
        Raises:
            HTTPException: 404 文章不存在
        """
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文章不存在",
            )
        # 普通用户只能看到已发布的文章
        if current_user.permission < PermissionLevel.SUPER_ADMIN:
            if db_post.status != "published":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文章不存在",
                )
        return db_post

    def favorite_blog_post(self, post_id: int, current_user: User) -> None:
        """
        收藏博客文章
        Args:
            post_id: 文章ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 文章不存在 / 400 已收藏
        """
        self._get_visible_blog_post(post_id, current_user)
        existing = favorite_crud.get_blog_post_favorite(
            self.db, current_user.id, post_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已收藏该文章",
            )
        favorite_crud.create_blog_post_favorite(self.db, current_user.id, post_id)

    def unfavorite_blog_post(self, post_id: int, current_user: User) -> None:
        """
        取消收藏博客文章
        Args:
            post_id: 文章ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 400 未收藏
        """
        existing = favorite_crud.get_blog_post_favorite(
            self.db, current_user.id, post_id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未收藏该文章",
            )
        favorite_crud.delete_blog_post_favorite(self.db, current_user.id, post_id)

    def list_blog_post_favorites(
        self, skip: int, limit: int, current_user: User
    ) -> BlogPostFavoriteListResponse:
        """
        获取当前用户的博客文章收藏列表
        Args:
            skip: 跳过数量
            limit: 限制数量
            current_user: 当前登录用户
        Returns:
            BlogPostFavoriteListResponse: 收藏列表
        """
        effective_status = "published" if current_user.permission < PermissionLevel.SUPER_ADMIN else None
        items, total = favorite_crud.get_user_blog_post_favorites(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=effective_status,
        )
        return BlogPostFavoriteListResponse(
            items=[BlogPostListItem.model_validate(post) for post in items],
            total=total,
        )

    # ---------- 分区关注 ----------

    def follow_zone(self, zone_id: int, current_user: User) -> None:
        """
        关注分区
        Args:
            zone_id: 分区ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 分区不存在 / 400 已关注
        """
        zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分区不存在",
            )
        existing = favorite_crud.get_zone_follow(self.db, current_user.id, zone_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已关注该分区",
            )
        favorite_crud.create_zone_follow(self.db, current_user.id, zone_id)

    def unfollow_zone(self, zone_id: int, current_user: User) -> None:
        """
        取消关注分区
        Args:
            zone_id: 分区ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 400 未关注
        """
        existing = favorite_crud.get_zone_follow(self.db, current_user.id, zone_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未关注该分区",
            )
        favorite_crud.delete_zone_follow(self.db, current_user.id, zone_id)

    def list_zone_follows(
        self, skip: int, limit: int, current_user: User
    ) -> ZoneFollowListResponse:
        """
        获取当前用户的分区关注列表
        Args:
            skip: 跳过数量
            limit: 限制数量
            current_user: 当前登录用户
        Returns:
            ZoneFollowListResponse: 关注列表
        """
        items, total = favorite_crud.get_user_zone_follows(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return ZoneFollowListResponse(
            items=[ForumZoneResponse.model_validate(zone) for zone in items],
            total=total,
        )

    # ---------- 论坛帖子收藏 ----------

    def favorite_post(self, post_id: int, current_user: User) -> None:
        """
        收藏论坛帖子
        Args:
            post_id: 帖子ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 帖子不存在 / 400 已收藏
        """
        post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帖子不存在",
            )
        existing = favorite_crud.get_post_favorite(self.db, current_user.id, post_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已收藏该帖子",
            )
        favorite_crud.create_post_favorite(self.db, current_user.id, post_id)

    def unfavorite_post(self, post_id: int, current_user: User) -> None:
        """
        取消收藏论坛帖子
        Args:
            post_id: 帖子ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 400 未收藏
        """
        existing = favorite_crud.get_post_favorite(self.db, current_user.id, post_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未收藏该帖子",
            )
        favorite_crud.delete_post_favorite(self.db, current_user.id, post_id)

    def list_post_favorites(
        self, skip: int, limit: int, current_user: User
    ) -> PostFavoriteListResponse:
        """
        获取当前用户的论坛帖子收藏列表
        Args:
            skip: 跳过数量
            limit: 限制数量
            current_user: 当前登录用户
        Returns:
            PostFavoriteListResponse: 收藏列表
        """
        items, total = favorite_crud.get_user_post_favorites(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        return PostFavoriteListResponse(
            items=[ForumPostResponse.model_validate(post) for post in items],
            total=total,
        )
