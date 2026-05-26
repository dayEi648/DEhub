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

logger = logging.getLogger(__name__)


class ForumReplyService:
    def __init__(self, db: Session):
        self.db = db

    def _can_modify_reply(
        self, reply: ForumReply, current_user: User
    ) -> None:
        """
        校验当前用户是否有权操作该回复
        作者本人 / 管理员 / 该回复所属帖子的分区区主
        Args:
            reply: 回复对象
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 回复所属帖子数据异常 / 403 权限不足
        """
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
        """
        发表回复（登录用户）
        user_id 强制从 current_user 注入
        Args:
            post_id: 帖子ID（来自路径参数）
            reply_in: 回复创建请求
            current_user: 当前登录用户
        Returns:
            ForumReply: 回复对象
        Raises:
            HTTPException: 404 帖子不存在
        """
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

        # 重新查询以加载 user 关联，避免延迟加载问题
        refreshed = forum_reply_crud.get_reply_by_id(self.db, db_reply.id)

        ForumCacheInvalidator.invalidate_forum_posts(zone_id=post.zone_id)
        return refreshed

    def delete_reply(self, reply_id: int, current_user: User) -> None:
        """
        删除回复（作者本人 或 管理员 或 区主）
        删除前会先级联删除该回复下的所有评论。
        Args:
            reply_id: 回复ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 回复不存在 / 403 权限不足
        """
        db_reply = forum_reply_crud.get_reply_by_id(self.db, reply_id)
        if not db_reply:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="回复不存在"
            )

        self._can_modify_reply(db_reply, current_user)

        # 级联清理该 reply 正文中的内嵌 OSS 图片，实际删除在数据库删除成功后执行。
        image_urls = extract_oss_image_urls_from_markdown(db_reply.content)
        file_paths_to_delete = [
            convert_oss_url_to_file_path(url)
            for url in image_urls
        ]

        # 级联删除该 reply 下的所有评论
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

            # 级联删除该回复的点赞记录
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
        """
        分页查询某帖子下的回复列表（补充当前用户点赞状态）
        Args:
            post_id: 帖子ID
            skip: 跳过数量
            limit: 限制数量
            current_user: 当前登录用户
        Returns:
            tuple[list[ForumReplyResponse], int]: 回复列表与总条数
        Raises:
            HTTPException: 404 帖子不存在
        """
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
        """
        点赞回复
        Args:
            reply_id: 回复ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 回复不存在 或 400 已点赞
        """
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
            # 数据库触发器会自动维护 likecount
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已点赞该回复",
            )

    def unlike_reply(self, reply_id: int, current_user: User) -> None:
        """
        取消点赞回复
        Args:
            reply_id: 回复ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 回复不存在 或 400 未点赞
        """
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
        # 数据库触发器会自动维护 likecount
