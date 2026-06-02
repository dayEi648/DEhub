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
from app.infrastructure.cache import build_cache_key, get_json_cache, set_json_cache
from app.infrastructure.cache_invalidator import UserCacheInvalidator
from app.core.config import settings


class UserFavoriteService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 博客文章收藏 ----------

    def _get_visible_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文章不存在",
            )
        if current_user.permission < PermissionLevel.SUPER_ADMIN:
            if db_post.status != "published":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文章不存在",
                )
        return db_post

    def favorite_blog_post(self, post_id: int, current_user: User) -> None:
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
        UserCacheInvalidator.invalidate_blog_post_favorites(current_user.id)

    def unfavorite_blog_post(self, post_id: int, current_user: User) -> None:
        existing = favorite_crud.get_blog_post_favorite(
            self.db, current_user.id, post_id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未收藏该文章",
            )
        favorite_crud.delete_blog_post_favorite(self.db, current_user.id, post_id)
        UserCacheInvalidator.invalidate_blog_post_favorites(current_user.id)

    def is_blog_post_favorited(self, post_id: int, current_user: User) -> bool:
        self._get_visible_blog_post(post_id, current_user)
        existing = favorite_crud.get_blog_post_favorite(
            self.db, current_user.id, post_id
        )
        return existing is not None

    def list_blog_post_favorites(
        self, skip: int, limit: int, current_user: User
    ) -> BlogPostFavoriteListResponse:
        cache_key = build_cache_key(
            "favorites:blog_posts:user",
            {"user_id": current_user.id, "skip": skip, "limit": limit},
        )
        cached = get_json_cache(cache_key, BlogPostFavoriteListResponse)
        if cached is not None:
            return cached

        effective_status = "published" if current_user.permission < PermissionLevel.SUPER_ADMIN else None
        items, total = favorite_crud.get_user_blog_post_favorites(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=effective_status,
        )
        result = BlogPostFavoriteListResponse(
            items=[BlogPostListItem.model_validate(post) for post in items],
            total=total,
        )
        set_json_cache(
            cache_key, result, settings.CACHE_DEFAULT_TTL, tags=["favorites"]
        )
        return result

    # ---------- 分区关注 ----------

    def follow_zone(self, zone_id: int, current_user: User) -> None:
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
        UserCacheInvalidator.invalidate_zone_follows(current_user.id)

    def unfollow_zone(self, zone_id: int, current_user: User) -> None:
        existing = favorite_crud.get_zone_follow(self.db, current_user.id, zone_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未关注该分区",
            )
        favorite_crud.delete_zone_follow(self.db, current_user.id, zone_id)
        UserCacheInvalidator.invalidate_zone_follows(current_user.id)

    def list_zone_follows(
        self, skip: int, limit: int, current_user: User
    ) -> ZoneFollowListResponse:
        cache_key = build_cache_key(
            "follows:zones:user",
            {"user_id": current_user.id, "skip": skip, "limit": limit},
        )
        cached = get_json_cache(cache_key, ZoneFollowListResponse)
        if cached is not None:
            return cached

        items, total = favorite_crud.get_user_zone_follows(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        result = ZoneFollowListResponse(
            items=[ForumZoneResponse.model_validate(zone) for zone in items],
            total=total,
        )
        set_json_cache(
            cache_key, result, settings.CACHE_DEFAULT_TTL, tags=["follows"]
        )
        return result

    # ---------- 论坛帖子收藏 ----------

    def favorite_post(self, post_id: int, current_user: User) -> None:
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
        UserCacheInvalidator.invalidate_forum_post_favorites(current_user.id)

    def unfavorite_post(self, post_id: int, current_user: User) -> None:
        existing = favorite_crud.get_post_favorite(self.db, current_user.id, post_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未收藏该帖子",
            )
        favorite_crud.delete_post_favorite(self.db, current_user.id, post_id)
        UserCacheInvalidator.invalidate_forum_post_favorites(current_user.id)

    def is_post_favorited(self, post_id: int, current_user: User) -> bool:
        post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="帖子不存在",
            )
        existing = favorite_crud.get_post_favorite(
            self.db, current_user.id, post_id
        )
        return existing is not None

    def list_post_favorites(
        self, skip: int, limit: int, current_user: User
    ) -> PostFavoriteListResponse:
        cache_key = build_cache_key(
            "favorites:forum_posts:user",
            {"user_id": current_user.id, "skip": skip, "limit": limit},
        )
        cached = get_json_cache(cache_key, PostFavoriteListResponse)
        if cached is not None:
            return cached

        items, total = favorite_crud.get_user_post_favorites(
            self.db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
        )
        result = PostFavoriteListResponse(
            items=[ForumPostResponse.model_validate(post) for post in items],
            total=total,
        )
        set_json_cache(
            cache_key, result, settings.CACHE_DEFAULT_TTL, tags=["favorites"]
        )
        return result

    # ---------- 供 LLM Tools 调用的辅助方法（接受 user_id，不依赖 User 对象）----------

    def favorite_blog_post_by_slug(self, slug: str, user_id: int) -> None:
        """通过 slug 收藏博客文章。"""
        db_post = blog_post_crud.get_blog_post_by_slug(self.db, slug)
        if not db_post or db_post.status != "published":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文章不存在",
            )
        existing = favorite_crud.get_blog_post_favorite(
            self.db, user_id, db_post.id
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已收藏该文章",
            )
        favorite_crud.create_blog_post_favorite(self.db, user_id, db_post.id)
        UserCacheInvalidator.invalidate_blog_post_favorites(user_id)

    def unfavorite_blog_post_by_slug(self, slug: str, user_id: int) -> None:
        """通过 slug 取消收藏博客文章。"""
        db_post = blog_post_crud.get_blog_post_by_slug(self.db, slug)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文章不存在",
            )
        existing = favorite_crud.get_blog_post_favorite(
            self.db, user_id, db_post.id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未收藏该文章",
            )
        favorite_crud.delete_blog_post_favorite(self.db, user_id, db_post.id)
        UserCacheInvalidator.invalidate_blog_post_favorites(user_id)

    def follow_zone_by_id(self, zone_id: int, user_id: int) -> None:
        """通过分区 ID 关注分区。"""
        zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分区不存在",
            )
        existing = favorite_crud.get_zone_follow(self.db, user_id, zone_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已关注该分区",
            )
        favorite_crud.create_zone_follow(self.db, user_id, zone_id)
        UserCacheInvalidator.invalidate_zone_follows(user_id)

    def unfollow_zone_by_id(self, zone_id: int, user_id: int) -> None:
        """通过分区 ID 取消关注分区。"""
        existing = favorite_crud.get_zone_follow(self.db, user_id, zone_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未关注该分区",
            )
        favorite_crud.delete_zone_follow(self.db, user_id, zone_id)
        UserCacheInvalidator.invalidate_zone_follows(user_id)
