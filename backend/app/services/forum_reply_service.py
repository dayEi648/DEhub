from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.forum_reply import ForumReply
from app.schemas.forum_reply import ForumReplyCreate, ForumReplyResponse
from app.crud import forum_reply as forum_reply_crud
from app.crud import forum_post as forum_post_crud
from app.crud import comment as comment_crud
from app.core.zone_manager import is_zone_manager


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
        is_admin = current_user.permission >= 1
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

        db_reply = forum_reply_crud.create_reply(
            self.db, reply_in, current_user.id
        )
        forum_post_crud.increment_reply_count(self.db, post_id)
        # 重新查询以加载 user 关联，避免延迟加载问题
        refreshed = forum_reply_crud.get_reply_by_id(self.db, db_reply.id)
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

        # 级联删除该 reply 下的所有评论
        reply_comments, _ = comment_crud.get_comments(
            self.db,
            target_type="forum_reply",
            target_id=reply_id,
            limit=10000,  # 足够大的上限以覆盖所有评论
        )
        if reply_comments:
            comment_ids = [c.id for c in reply_comments]
            comment_crud.delete_comment_likes_by_comment_ids(self.db, comment_ids)
            comment_crud.delete_comments_by_ids(self.db, comment_ids)

        forum_reply_crud.delete_reply(self.db, reply_id)
        forum_post_crud.decrement_reply_count(self.db, db_reply.post_id)

    def list_replies_by_post(
        self, post_id: int, skip: int, limit: int
    ) -> tuple[list[ForumReply], int]:
        """
        分页查询某帖子下的回复列表
        Args:
            post_id: 帖子ID
            skip: 跳过数量
            limit: 限制数量
        Returns:
            tuple[list[ForumReply], int]: 回复列表与总条数
        Raises:
            HTTPException: 404 帖子不存在
        """
        post = forum_post_crud.get_post_by_id(self.db, post_id)
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在"
            )

        return forum_reply_crud.get_replies_by_post_id(
            self.db, post_id=post_id, skip=skip, limit=limit
        )
