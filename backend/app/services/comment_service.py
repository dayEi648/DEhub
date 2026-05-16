from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.comment import Comment
from app.schemas.comment import CommentCreate
from app.crud import comment as comment_crud
from app.crud import blog_post as blog_post_crud
from app.crud import forum_reply as forum_reply_crud


# 可扩展的 target_type 校验器：新增场景时追加键值对即可
TARGET_TYPE_VALIDATORS = {
    "blog_post": lambda db, target_id: blog_post_crud.get_blog_post_by_id(db, target_id),
    "forum_reply": lambda db, target_id: forum_reply_crud.get_reply_by_id(db, target_id),
}


class CommentService:
    def __init__(self, db: Session):
        """
        初始化 CommentService
        Args:
            db: 数据库会话
        """
        self.db = db

    def _validate_target(self, target_type: str, target_id: int) -> None:
        """
        校验 target_type 是否在白名单中，且对应实体真实存在
        Args:
            target_type: 目标类型
            target_id: 目标ID
        Raises:
            HTTPException: 400 类型非法 或 404 目标不存在
        """
        validator = TARGET_TYPE_VALIDATORS.get(target_type)
        if validator is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的评论目标类型: {target_type}",
            )
        target = validator(self.db, target_id)
        if target is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论目标不存在",
            )

    def _require_owner_or_admin(
        self, current_user: User, comment_user_id: int
    ) -> None:
        """
        要求当前用户为评论作者本人，或管理员及以上权限
        Args:
            current_user: 当前登录用户
            comment_user_id: 评论作者用户ID
        Raises:
            HTTPException: 403 权限不足
        """
        if current_user.id != comment_user_id and current_user.permission < 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权操作此评论",
            )

    def create_comment(
        self, comment_in: CommentCreate, current_user: User
    ) -> Comment:
        """
        新增评论
        Args:
            comment_in: 评论创建请求
            current_user: 当前登录用户
        Returns:
            Comment: 评论对象（已加载 user 关联）
        """
        self._validate_target(comment_in.target_type, comment_in.target_id)
        db_comment = comment_crud.create_comment(self.db, comment_in, current_user.id)
        # 重新查询以加载 user 关联，避免延迟加载问题
        refreshed = comment_crud.get_comment_by_id(self.db, db_comment.id)
        return refreshed

    def delete_comment(self, comment_id: int, current_user: User) -> None:
        """
        删除评论
        Args:
            comment_id: 评论ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 评论不存在 或 403 权限不足
        """
        db_comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if db_comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        self._require_owner_or_admin(current_user, db_comment.user_id)
        comment_crud.delete_comment(self.db, comment_id)

    def list_comments(
        self,
        target_type: str,
        target_id: int,
        parent_id: int | None,
        sort_by: str,
        skip: int,
        limit: int,
    ) -> tuple[list[Comment], int]:
        """
        分页查询评论列表
        Args:
            target_type: 目标类型
            target_id: 目标ID
            parent_id: 父评论ID
            sort_by: 排序方式
            skip: 跳过数量
            limit: 限制数量
        Returns:
            tuple[list[Comment], int]: 评论列表与总条数
        """
        return comment_crud.get_comments(
            self.db,
            target_type=target_type,
            target_id=target_id,
            parent_id=parent_id,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
        )

    def like_comment(self, comment_id: int, current_user: User) -> None:
        """
        点赞评论
        Args:
            comment_id: 评论ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 评论不存在 或 400 已点赞
        """
        db_comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if db_comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        existing = comment_crud.get_user_comment_like(
            self.db, comment_id, current_user.id
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已点赞该评论",
            )
        comment_crud.create_user_comment_like(self.db, comment_id, current_user.id)
        db_comment.likecount += 1
        self.db.commit()

    def unlike_comment(self, comment_id: int, current_user: User) -> None:
        """
        取消点赞评论
        Args:
            comment_id: 评论ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 评论不存在 或 400 未点赞
        """
        db_comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if db_comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        existing = comment_crud.get_user_comment_like(
            self.db, comment_id, current_user.id
        )
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未点赞该评论",
            )
        comment_crud.delete_user_comment_like(self.db, comment_id, current_user.id)
        db_comment.likecount -= 1
        self.db.commit()
