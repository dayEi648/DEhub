from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import re

from app.core.permissions import require_owner_or_admin
from app.models.user import User
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentResponse
from app.crud import comment as comment_crud
from app.crud import blog_post as blog_post_crud
from app.crud import forum_reply as forum_reply_crud
from app.infrastructure.cache_invalidator import BlogCacheInvalidator


TARGET_TYPE_VALIDATORS = {
    "blog_post": lambda db, target_id: blog_post_crud.get_blog_post_by_id(db, target_id),
    "forum_reply": lambda db, target_id: forum_reply_crud.get_reply_by_id(db, target_id),
}

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_HTML_IMAGE_RE = re.compile(r"<img\s+[^>]*src\s*=\s*['\"][^'\"]+['\"][^>]*>", re.IGNORECASE)


class CommentService:
    def __init__(self, db: Session):
        self.db = db

    def _validate_target(self, target_type: str, target_id: int) -> None:
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

    def _validate_comment_create(self, comment_in: CommentCreate) -> CommentCreate:
        if _MARKDOWN_IMAGE_RE.search(comment_in.content) or _HTML_IMAGE_RE.search(comment_in.content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="评论内容不支持内嵌图片",
            )

        if not comment_in.is_nested and comment_in.nested_parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="非嵌套回复不能指定 nested_parent_id",
            )

        if comment_in.target_type == "forum_reply" and comment_in.parent_id is None:
            comment_in = CommentCreate(
                target_type=comment_in.target_type,
                target_id=comment_in.target_id,
                parent_id=comment_in.target_id,
                is_nested=comment_in.is_nested,
                nested_parent_id=comment_in.nested_parent_id,
                content=comment_in.content,
            )

        if comment_in.parent_id is None and comment_in.is_nested:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="嵌套回复必须指定 parent_id",
            )

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
                if parent_comment.parent_id is not None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="博客场景下 parent_id 必须指向表层评论",
                    )
                if (
                    parent_comment.target_type != comment_in.target_type
                    or parent_comment.target_id != comment_in.target_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="parent_id 对应的评论与当前评论目标不一致",
                    )

        elif comment_in.target_type == "forum_reply":
            if comment_in.parent_id != comment_in.target_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="论坛场景下 parent_id 必须等于 target_id",
                )

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
            if (
                nested_target.target_type != comment_in.target_type
                or nested_target.target_id != comment_in.target_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="nested_parent_id 对应的评论与当前评论目标不一致",
                )
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
        self._validate_target(comment_in.target_type, comment_in.target_id)
        comment_in = self._validate_comment_create(comment_in)
        db_comment = comment_crud.create_comment(self.db, comment_in, current_user.id)

        if comment_in.target_type == "blog_post":
            BlogCacheInvalidator.invalidate_blog_posts()

        refreshed = comment_crud.get_comment_by_id(self.db, db_comment.id)
        return refreshed

    def delete_comment(self, comment_id: int, current_user: User) -> None:
        db_comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if db_comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        target_type = db_comment.target_type

        try:
            require_owner_or_admin(current_user, db_comment.user_id)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail="无权操作此评论",
            ) from exc

        if target_type == "blog_post" and db_comment.parent_id is None:
            child_comments = comment_crud.get_comments_by_parent_id(
                self.db, comment_id
            )
            child_ids = [c.id for c in child_comments]
            if child_ids:
                comment_crud.delete_comment_likes_by_comment_ids(self.db, child_ids)
                comment_crud.delete_comments_by_ids(self.db, child_ids)

        comment_crud.delete_comment(self.db, comment_id)

        if target_type == "blog_post":
            BlogCacheInvalidator.invalidate_blog_posts()

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

    def like_comment(self, comment_id: int, current_user: User) -> dict:
        comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        db_like = comment_crud.get_user_comment_like(
            self.db, current_user.id, comment_id
        )
        if db_like is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="已点赞此评论",
            )

        comment_crud.create_user_comment_like(self.db, current_user.id, comment_id)

        return {"message": "点赞成功"}

    def unlike_comment(self, comment_id: int, current_user: User) -> dict:
        comment = comment_crud.get_comment_by_id(self.db, comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="评论不存在",
            )
        db_like = comment_crud.get_user_comment_like(
            self.db, current_user.id, comment_id
        )
        if db_like is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="未点赞此评论",
            )

        comment_crud.delete_user_comment_like(self.db, current_user.id, comment_id)

        return {"message": "取消点赞成功"}
