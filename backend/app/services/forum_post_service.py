from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.forum_post import ForumPost
from app.core.permissions import require_admin
from app.schemas.forum_post import ForumPostCreate, ForumPostUpdate, ForumPostResponse
from app.crud import forum_post as forum_post_crud
from app.crud import forum_zone as forum_zone_crud
from app.core.zone_manager import is_zone_manager


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
        is_admin = current_user.permission >= 1
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

        return forum_post_crud.create_post(self.db, post_in, current_user.id)

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
        return forum_post_crud.update_post(self.db, db_post, post_in)

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
        forum_post_crud.delete_post(self.db, post_id)

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
    ) -> list[ForumPost]:
        """
        获取帖子列表（支持分区筛选、排序与分页）
        Args:
            zone_id: 分区ID筛选
            sort_by: 排序方式，"created" 或 "view"
            skip: 跳过数量
            limit: 限制数量
        Returns:
            list[ForumPost]: 帖子列表
        Raises:
            HTTPException: 404 分区不存在
        """
        if zone_id is not None:
            zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
            if not zone:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
                )

        return forum_post_crud.get_posts(
            self.db, zone_id=zone_id, sort_by=sort_by, skip=skip, limit=limit
        )
