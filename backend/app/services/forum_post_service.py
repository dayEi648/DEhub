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
from app.core.config import settings
from app.storage.oss import (
    convert_oss_url_to_file_path,
    delete_file_from_oss_sync,
    extract_oss_image_urls_from_markdown,
)

logger = logging.getLogger(__name__)


class ForumPostService:
    def __init__(self, db: Session):
        self.db = db

    def _can_modify_post(
        self, post: ForumPost, current_user: User, allow_manager: bool = False
    ) -> None:
        """
        校验当前用户是否有权操作该帖子
        Args:
            post: 帖子对象
            current_user: 当前登录用户
            allow_manager: 是否允许区主拥有权限
        Raises:
            HTTPException: 403 权限不足
        """
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
        """
        发表帖子（登录用户）
        user_id 强制从 current_user 注入，禁止伪造
        Args:
            post_in: 帖子创建请求
            current_user: 当前登录用户
        Returns:
            ForumPost: 帖子对象
        Raises:
            HTTPException: 404 分区不存在
        """
        zone = forum_zone_crud.get_zone_by_id(self.db, post_in.zone_id)
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )

        db_post = forum_post_crud.create_post(self.db, post_in, current_user.id)
        # 重新查询以加载 user 关联，避免延迟加载问题
        refreshed = forum_post_crud.get_post_by_id(self.db, db_post.id)

        ForumCacheInvalidator.invalidate_forum_posts(zone_id=post_in.zone_id)
        return refreshed

    def update_post(
        self, post_id: int, post_in: ForumPostUpdate, current_user: User
    ) -> ForumPost:
        """
        编辑帖子（作者本人 或 管理员及以上）
        区主无权编辑他人帖子
        Args:
            post_id: 帖子ID
            post_in: 帖子更新请求
            current_user: 当前登录用户
        Returns:
            ForumPost: 帖子对象
        Raises:
            HTTPException: 404 帖子不存在 / 403 权限不足
        """
        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        self._can_modify_post(db_post, current_user, allow_manager=False)
        old_zone_id = db_post.zone_id
        updated = forum_post_crud.update_post(self.db, db_post, post_in)

        ForumCacheInvalidator.invalidate_forum_posts_for_zone_change(
            old_zone_id=old_zone_id,
            new_zone_id=updated.zone_id,
        )
        return updated

    def delete_post(self, post_id: int, current_user: User) -> None:
        """
        删除帖子（作者本人 或 管理员 或 区主）
        Args:
            post_id: 帖子ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 帖子不存在 / 403 权限不足
        """
        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        self._can_modify_post(db_post, current_user, allow_manager=True)
        zone_id = db_post.zone_id

        # 预取回复（用于图片和评论级联清理）
        replies = forum_reply_crud.get_all_replies_by_post_id(
            self.db,
            post_id=post_id,
        )

        file_paths_to_delete: list[str] = []

        # 级联清理帖子正文中的内嵌 OSS 图片，实际删除在数据库删除成功后执行。
        post_image_urls = extract_oss_image_urls_from_markdown(db_post.content)
        for url in post_image_urls:
            file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        # 级联清理回复正文中的内嵌 OSS 图片，实际删除在数据库删除成功后执行。
        for reply in replies:
            reply_image_urls = extract_oss_image_urls_from_markdown(reply.content)
            for url in reply_image_urls:
                file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        # 级联删除该帖子下所有回复评论（comments 无外键约束，需显式删除）
        reply_ids = [reply.id for reply in replies]
        comment_ids = comment_crud.get_comment_ids_by_target_ids(
            self.db,
            target_type="forum_reply",
            target_ids=reply_ids,
        )
        if comment_ids:
            comment_crud.delete_comment_likes_by_comment_ids(self.db, comment_ids)
            comment_crud.delete_comments_by_ids(self.db, comment_ids)

        forum_post_crud.delete_post(self.db, post_id)
        ForumCacheInvalidator.invalidate_forum_posts(zone_id=zone_id)

        for file_path in file_paths_to_delete:
            try:
                delete_file_from_oss_sync(file_path)
            except Exception:
                logger.exception("删除论坛帖子关联 OSS 文件失败: post_id=%s, file=%s", post_id, file_path)

    def get_post(self, post_id: int) -> ForumPost:
        """
        获取帖子详情（同时增加浏览量）
        Args:
            post_id: 帖子ID
        Returns:
            ForumPost: 帖子对象
        Raises:
            HTTPException: 404 帖子不存在
        """
        db_post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        forum_post_crud.increment_post_view_count(self.db, post_id)
        return db_post

    def list_posts(
        self,
        zone_id: int | None,
        sort_by: str,
        skip: int,
        limit: int,
    ) -> ForumPostListResponse:
        """
        获取帖子列表（支持分区筛选、排序与分页）
        Args:
            zone_id: 分区ID筛选
            sort_by: 排序方式，"created" 或 "view"
            skip: 跳过数量
            limit: 限制数量
        Returns:
            ForumPostListResponse: 帖子分页列表
        Raises:
            HTTPException: 404 分区不存在
        """
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
            ttl = settings.CACHE_FORUM_HOT_POST_TTL  # 热门 30s
            is_hot_key = True
        else:
            ttl = settings.CACHE_FORUM_POST_LIST_TTL  # 普通 60s
            is_hot_key = False

        cached = get_json_cache(cache_key, ForumPostListResponse)
        if cached is not None:
            return cached

        # 热门 key 加短锁防击穿
        lock_token = None
        if is_hot_key:
            lock_token = acquire_cache_lock(cache_key, ttl=5)

        items, total = forum_post_crud.get_posts(
            self.db, zone_id=zone_id, sort_by=sort_by, skip=skip, limit=limit
        )
        result = ForumPostListResponse(
            items=[ForumPostListItem.model_validate(post) for post in items],
            total=total,
        )

        tags = ["forum_posts"]
        if zone_id is not None:
            tags.append(f"forum_posts:zone:{zone_id}")

        # 热门 key 只有抢到锁才写缓存；普通 key 直接写
        if not is_hot_key or lock_token is not None:
            set_json_cache(cache_key, result, ttl, tags=tags)
        if lock_token is not None:
            release_cache_lock(cache_key, lock_token)

        return result
