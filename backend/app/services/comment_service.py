from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import re

from app.core.permissions import require_owner_or_admin
from app.models.user import User
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse
from app.crud import comment as comment_crud
from app.crud import blog_post as blog_post_crud
from app.crud import forum_reply as forum_reply_crud


# 可扩展的 target_type 校验器：新增场景时追加键值对即可
TARGET_TYPE_VALIDATORS = {
    "blog_post": lambda db, target_id: blog_post_crud.get_blog_post_by_id(db, target_id),
    "forum_reply": lambda db, target_id: forum_reply_crud.get_reply_by_id(db, target_id),
}

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_HTML_IMAGE_RE = re.compile(r"<img\s+[^>]*src\s*=\s*['\"][^'\"]+['\"][^>]*>", re.IGNORECASE)


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
        try:
            require_owner_or_admin(current_user, comment_user_id)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail="无权操作此评论",
            ) from exc

    def _validate_comment_create(self, comment_in: CommentCreate) -> CommentCreate:
        """
        校验并规范化评论创建请求
        Args:
            comment_in: 评论创建请求
        Returns:
            CommentCreate: 规范化后的请求
        Raises:
            HTTPException: 参数非法
        """
        # 评论内容不允许内嵌图片（Markdown 图片语法或 HTML img 标签）
        if _MARKDOWN_IMAGE_RE.search(comment_in.content) or _HTML_IMAGE_RE.search(comment_in.content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="评论内容不支持内嵌图片",
            )

        # 规则1：is_nested=False 时 nested_parent_id 必须为 None
        if not comment_in.is_nested and comment_in.nested_parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="非嵌套回复不能指定 nested_parent_id",
            )

        # 论坛场景：若未传 parent_id，自动设置为 target_id
        if comment_in.target_type == "forum_reply" and comment_in.parent_id is None:
            comment_in = CommentCreate(
                target_type=comment_in.target_type,
                target_id=comment_in.target_id,
                parent_id=comment_in.target_id,
                is_nested=comment_in.is_nested,
                nested_parent_id=comment_in.nested_parent_id,
                content=comment_in.content,
            )

        # 规则2：parent_id 为 None 时 is_nested 必须为 False
        if comment_in.parent_id is None and comment_in.is_nested:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="嵌套回复必须指定 parent_id",
            )

        # 博客场景校验
        if comment_in.target_type == "blog_post":
            if comment_in.parent_id is not None:
                parent_comment = comment_crud.get_comment_by_id(
                    self.db, comment_in.parent_id
                )
                if parent_comment is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="parent_id 对应的评论不存在",
                    )
                # 博客里层/嵌套回复的 parent_id 必须指向表层评论
                if parent_comment.parent_id is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="博客场景下 parent_id 必须指向表层评论",
                    )
                # target 一致性校验
                if (
                    parent_comment.target_type != comment_in.target_type
                    or parent_comment.target_id != comment_in.target_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="parent_id 对应的评论与当前评论目标不一致",
                    )

        # 论坛场景校验
        elif comment_in.target_type == "forum_reply":
            if comment_in.parent_id != comment_in.target_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="论坛场景下 parent_id 必须等于 target_id",
                )

        # 嵌套回复校验
        if comment_in.is_nested:
            if comment_in.nested_parent_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="嵌套回复必须指定 nested_parent_id",
                )
            nested_target = comment_crud.get_comment_by_id(
                self.db, comment_in.nested_parent_id
            )
            if nested_target is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="nested_parent_id 对应的评论不存在",
                )
            if nested_target.is_nested:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="nested_parent_id 不能指向另一条嵌套回复",
                )
            # target 一致性校验
            if (
                nested_target.target_type != comment_in.target_type
                or nested_target.target_id != comment_in.target_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="nested_parent_id 对应的评论与当前评论目标不一致",
                )
            # 博客场景：nested_parent_id 必须指向同一表层评论下的里层回复
            if comment_in.target_type == "blog_post":
                if nested_target.parent_id != comment_in.parent_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="nested_parent_id 必须与 parent_id 指向同一表层评论",
                    )

        return comment_in

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
        comment_in = self._validate_comment_create(comment_in)
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

        # 若删除的是博客表层评论，先级联删除其下所有里层回复与嵌套回复
        if db_comment.target_type == "blog_post" and db_comment.parent_id is None:
            child_comments = comment_crud.get_comments_by_parent_id(
                self.db, comment_id
            )
            child_ids = [c.id for c in child_comments]
            if child_ids:
                # 先批量删除点赞记录（避免外键约束问题）
                comment_crud.delete_comment_likes_by_comment_ids(self.db, child_ids)
                # 批量删除子评论（嵌套回复由 nested_parent_id 的级联外键自动处理）
                comment_crud.delete_comments_by_ids(self.db, child_ids)

        comment_crud.delete_comment(self.db, comment_id)

    def list_comments(
        self,
        target_type: str,
        target_id: int,
        parent_id: int | None,
        is_nested: bool | None,
        nested_parent_id: int | None,
        sort_by: str,
        skip: int,
        limit: int,
    ) -> tuple[list[Comment], int]:
        """
        分页查询评论列表
        Args:
            target_type: 目标类型
            target_id: 目标ID
            parent_id: 父级ID
            is_nested: 是否嵌套回复
            nested_parent_id: 嵌套父级ID
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
            is_nested=is_nested,
            nested_parent_id=nested_parent_id,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
        )

    def list_comments_with_like_state(
        self,
        target_type: str,
        target_id: int,
        parent_id: int | None,
        is_nested: bool | None,
        nested_parent_id: int | None,
        sort_by: str,
        skip: int,
        limit: int,
        current_user: User,
    ) -> tuple[list[CommentResponse], int]:
        """
        查询评论并补充当前用户的点赞状态。
        """
        items, total = self.list_comments(
            target_type=target_type,
            target_id=target_id,
            parent_id=parent_id,
            is_nested=is_nested,
            nested_parent_id=nested_parent_id,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
        )
        responses = [CommentResponse.model_validate(item) for item in items]
        if not responses:
            return responses, total

        liked_ids = comment_crud.get_user_liked_comment_ids(
            self.db,
            current_user.id,
            [item.id for item in items],
        )
        for response in responses:
            response.is_liked = response.id in liked_ids
        return responses, total

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
        try:
            comment_crud.create_user_comment_like(self.db, comment_id, current_user.id)
            # 数据库触发器会自动维护 likecount，Service 层不再手动操作
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已点赞该评论",
            )

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
        # 数据库触发器会自动维护 likecount，Service 层不再手动操作
