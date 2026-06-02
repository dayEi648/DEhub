from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import logging

from app.models.user import User
from app.models.forum_reply import ForumReply
from app.core.permission_levels import PermissionLevel
from app.schemas.forum_reply import ForumReplyCreate, ForumReplyResponse
from app.crud import forum_reply as forum_reply_crud
from app.crud import forum_post as forum_post_crud
from app.crud import comment as comment_crud
from app.core.zone_manager import is_zone_manager
from app.infrastructure.cache_invalidator import ForumCacheInvalidator
from app.storage.oss import convert_oss_url_to_file_path, extract_oss_image_urls_from_markdown
from app.services.oss_cleanup_service import OssCleanupService
from app.services.content_moderation_service import ContentModerationService

logger = logging.getLogger(__name__)


def _build_reply_snapshot(reply: ForumReply) -> dict[str, str]:
    """构建论坛回复的审核字段快照。"""
    return {"content": reply.content}


class ForumReplyService:
    def __init__(self, db: Session):
        self.db = db

    def _can_modify_reply(
        self, reply: ForumReply, current_user: User
    ) -> None:
        post = forum_post_crud.get_post_by_id(self.db, reply.post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回复所属帖子数据异常",
            )

        is_owner = reply.user_id == current_user.id
        is_admin = current_user.permission >= PermissionLevel.ADMIN
        is_manager = is_zone_manager(self.db, post.zone_id, current_user.id)

        if not (is_owner or is_admin or is_manager):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此回复"
            )

    def create_reply(
        self, post_id: int, reply_in: ForumReplyCreate, current_user: User
    ) -> ForumReply:
        post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        try:
            db_reply = forum_reply_crud.create_reply(
                self.db, reply_in, current_user.id, auto_commit=False
            )
            forum_post_crud.increment_reply_count(
                self.db, post_id, auto_commit=False
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        refreshed = forum_reply_crud.get_reply_by_id(self.db, db_reply.id)

        # 触发内容审核
        self.db.refresh(refreshed)
        ContentModerationService(self.db).enqueue(
            target_type="forum_reply",
            target_id=refreshed.id,
            target_version=refreshed.updated_at.isoformat(),
            trigger_action="create",
            snapshot=_build_reply_snapshot(refreshed),
            created_by_user_id=current_user.id,
        )

        ForumCacheInvalidator.invalidate_forum_posts(zone_id=post.zone_id)
        return refreshed

    def delete_reply(self, reply_id: int, current_user: User) -> None:
        db_reply = forum_reply_crud.get_reply_by_id(self.db, reply_id)
        if not db_reply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="回复不存在"
            )

        self._can_modify_reply(db_reply, current_user)

        image_urls = extract_oss_image_urls_from_markdown(db_reply.content)
        file_paths_to_delete = [
            convert_oss_url_to_file_path(url)
            for url in image_urls
        ]

        comment_ids = comment_crud.get_comment_ids_by_target_ids(
            self.db,
            target_type="forum_reply",
            target_ids=[reply_id],
        )
        post = forum_post_crud.get_post_by_id(self.db, db_reply.post_id)
        try:
            if comment_ids:
                comment_crud.delete_comment_likes_by_comment_ids(
                    self.db, comment_ids, auto_commit=False
                )
                comment_crud.delete_comments_by_ids(
                    self.db, comment_ids, auto_commit=False
                )

            forum_reply_crud.delete_forum_reply_likes_by_reply_ids(
                self.db, [reply_id], auto_commit=False
            )
            forum_reply_crud.delete_reply(self.db, reply_id, auto_commit=False)
            forum_post_crud.decrement_reply_count(
                self.db, db_reply.post_id, auto_commit=False
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        if post:
            ForumCacheInvalidator.invalidate_forum_posts(zone_id=post.zone_id)

        cleanup_service = OssCleanupService()
        for file_path in file_paths_to_delete:
            cleanup_service.delete_file_after_commit_sync(
                file_path,
                source="forum.reply.delete",
            )

    def list_replies_by_post(
        self, post_id: int, skip: int, limit: int, current_user: User
    ) -> tuple[list[ForumReplyResponse], int]:
        post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        items, total = forum_reply_crud.get_replies_by_post_id(
            self.db, post_id=post_id, skip=skip, limit=limit
        )
        responses = [ForumReplyResponse.model_validate(item) for item in items]
        if not responses:
            return responses, total

        liked_ids = forum_reply_crud.get_user_liked_reply_ids(
            self.db,
            current_user.id,
            [item.id for item in items],
        )
        for response in responses:
            response.is_liked = response.id in liked_ids
        return responses, total

    def like_reply(self, reply_id: int, current_user: User) -> None:
        db_reply = forum_reply_crud.get_reply_by_id(self.db, reply_id)
        if not db_reply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回复不存在",
            )
        try:
            forum_reply_crud.create_user_forum_reply_like(
                self.db, reply_id, current_user.id
            )
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已点赞该回复",
            )

    def unlike_reply(self, reply_id: int, current_user: User) -> None:
        db_reply = forum_reply_crud.get_reply_by_id(self.db, reply_id)
        if not db_reply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="回复不存在",
            )
        existing = forum_reply_crud.get_user_forum_reply_like(
            self.db, reply_id, current_user.id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未点赞该回复",
            )
        forum_reply_crud.delete_user_forum_reply_like(
            self.db, reply_id, current_user.id
        )
