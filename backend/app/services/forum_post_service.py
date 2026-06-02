from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.models.user import User
from app.models.forum_post import ForumPost
from app.core.permission_levels import PermissionLevel
from app.schemas.forum_post import ForumPostCreate, ForumPostUpdate, ForumPostResponse, ForumPostListResponse, ForumPostListItem
from app.crud import forum_post as forum_post_crud
from app.crud import forum_reply as forum_reply_crud
from app.crud import forum_zone as forum_zone_crud
from app.crud import comment as comment_crud
from app.core.zone_manager import is_zone_manager
from app.infrastructure.cache import (
    build_cache_key,
    get_json_cache,
    set_json_cache,
    acquire_cache_lock,
    release_cache_lock,
)
from app.infrastructure.cache_invalidator import ForumCacheInvalidator
from app.infrastructure.view_counter import ViewCounter
from app.core.config import settings
from app.storage.oss import convert_oss_url_to_file_path, extract_oss_image_urls_from_markdown
from app.services.oss_cleanup_service import OssCleanupService

logger = logging.getLogger(__name__)


class ForumPostService:
    def __init__(self, db: Session):
        self.db = db

    def _can_modify_post(
        self, post: ForumPost, current_user: User, allow_manager: bool = False
    ) -> None:
        is_owner = post.user_id == current_user.id
        is_admin = current_user.permission >= PermissionLevel.ADMIN
        is_manager = allow_manager and is_zone_manager(
            self.db, post.zone_id, current_user.id
        )

        if not (is_owner or is_admin or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此帖子"
            )

    def create_post(
        self, post_in: ForumPostCreate, current_user: User
    ) -> ForumPost:
        zone = forum_zone_crud.get_zone_by_id(self.db, post_in.zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )

        db_post = forum_post_crud.create_post(self.db, post_in, current_user.id)
        refreshed = forum_post_crud.get_post_by_id(self.db, db_post.id)

        ForumCacheInvalidator.invalidate_forum_posts(zone_id=post_in.zone_id)
        return refreshed

    def update_post(
        self, post_id: int, post_in: ForumPostUpdate, current_user: User
    ) -> ForumPost:
        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        self._can_modify_post(db_post, current_user, allow_manager=False)

        update_data = post_in.model_dump(exclude_unset=True)
        if "zone_id" in update_data and update_data["zone_id"] != db_post.zone_id:
            zone = forum_zone_crud.get_zone_by_id(self.db, update_data["zone_id"])
            if not zone:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
                )

        old_zone_id = db_post.zone_id
        updated = forum_post_crud.update_post(self.db, db_post, post_in)

        ForumCacheInvalidator.invalidate_forum_posts_for_zone_change(
            old_zone_id=old_zone_id,
            new_zone_id=updated.zone_id,
        )
        return updated

    def delete_post(self, post_id: int, current_user: User) -> None:
        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        self._can_modify_post(db_post, current_user, allow_manager=True)
        zone_id = db_post.zone_id

        replies = forum_reply_crud.get_all_replies_by_post_id(
            self.db,
            post_id=post_id,
        )

        file_paths_to_delete: list[str] = []

        post_image_urls = extract_oss_image_urls_from_markdown(db_post.content)
        for url in post_image_urls:
            file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        for reply in replies:
            reply_image_urls = extract_oss_image_urls_from_markdown(reply.content)
            for url in reply_image_urls:
                file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        reply_ids = [reply.id for reply in replies]
        comment_ids = comment_crud.get_comment_ids_by_target_ids(
            self.db,
            target_type="forum_reply",
            target_ids=reply_ids,
        )
        try:
            if comment_ids:
                comment_crud.delete_comment_likes_by_comment_ids(
                    self.db, comment_ids, auto_commit=False
                )
                comment_crud.delete_comments_by_ids(
                    self.db, comment_ids, auto_commit=False
                )

            forum_post_crud.delete_post(self.db, post_id, auto_commit=False)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        ForumCacheInvalidator.invalidate_forum_posts(zone_id=zone_id)

        cleanup_service = OssCleanupService()
        for file_path in file_paths_to_delete:
            cleanup_service.delete_file_after_commit_sync(
                file_path,
                source="forum.post.delete",
            )

    def get_post(self, post_id: int) -> ForumPostResponse:
        cache_key = build_cache_key("forum_posts:detail", {"post_id": post_id})
        cached = get_json_cache(cache_key, ForumPostResponse)
        if cached is not None:
            ViewCounter.incr_forum_post_view_count(post_id, self.db)
            merged_vc = ViewCounter.get_forum_post_view_count(post_id, cached.view_count)
            if merged_vc != cached.view_count:
                cached = cached.model_copy(update={"view_count": merged_vc})
            return cached

        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        ViewCounter.incr_forum_post_view_count(post_id, self.db)
        db_post.view_count = ViewCounter.get_forum_post_view_count(post_id, db_post.view_count)

        result = ForumPostResponse.model_validate(db_post)
        set_json_cache(
            cache_key, result, settings.CACHE_FORUM_POST_DETAIL_TTL, tags=["forum_posts"]
        )
        return result

    def list_posts(
        self,
        zone_id: int | None,
        sort_by: str,
        skip: int,
        limit: int,
    ) -> ForumPostListResponse:
        if zone_id is not None:
            zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
            if not zone:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
                )

        cache_params = {
            "zone_id": zone_id,
            "sort_by": sort_by,
            "skip": skip,
            "limit": limit,
        }
        cache_key = build_cache_key("forum_posts:list", cache_params)

        if sort_by == "view" and skip == 0:
            ttl = settings.CACHE_FORUM_HOT_POST_TTL
            is_hot_key = True
        else:
            ttl = settings.CACHE_FORUM_POST_LIST_TTL
            is_hot_key = False

        cached = get_json_cache(cache_key, ForumPostListResponse)
        if cached is not None:
            return cached

        lock_token = None
        if is_hot_key:
            lock_token = acquire_cache_lock(cache_key, ttl=5)

        items, total = forum_post_crud.get_posts(
            self.db, zone_id=zone_id, sort_by=sort_by, skip=skip, limit=limit
        )
        list_items = []
        for post in items:
            item = ForumPostListItem.model_validate(post)
            merged_view_count = ViewCounter.get_forum_post_view_count(post.id, post.view_count)
            if merged_view_count != post.view_count:
                item = item.model_copy(update={"view_count": merged_view_count})
            list_items.append(item)
        result = ForumPostListResponse(
            items=list_items,
            total=total,
        )

        tags = ["forum_posts"]
        if zone_id is not None:
            tags.append(f"forum_posts:zone:{zone_id}")

        if not is_hot_key or lock_token is not None:
            set_json_cache(cache_key, result, ttl, tags=tags)
        if lock_token is not None:
            release_cache_lock(cache_key, lock_token)

        return result
