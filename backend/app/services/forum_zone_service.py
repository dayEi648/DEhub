from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.core.permissions import require_admin
from app.core.permission_levels import PermissionLevel
from app.schemas.forum_zone import ForumZoneCreate, ForumZoneUpdate
from app.crud import forum_zone as forum_zone_crud
from app.crud import forum_post as forum_post_crud
from app.crud import user as user_crud
from app.utils.slug import generate_unique_slug
from app.core.zone_manager import (
    is_zone_manager,
    set_zone_manager_cache,
    delete_zone_manager_cache,
)


class ForumZoneService:
    def __init__(self, db: Session):
        self.db = db

    def _require_admin(self, current_user: User) -> None:
        """要求当前用户为管理员及以上"""
        require_admin(current_user)

    def _validate_manager_id(self, manager_id: int) -> None:
        """
        校验目标区主用户是否存在且未注销
        Args:
            manager_id: 用户ID
        Raises:
            HTTPException: 400 用户不存在或已注销
        """
        target_user = user_crud.get_user_by_id(self.db, manager_id)
        if target_user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的区主用户不存在",
            )
        if target_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定的区主用户已注销",
            )

    def _ensure_slug_unique(
        self, slug: str, exclude_zone_id: int | None = None
    ) -> None:
        """
        校验分区 slug 唯一性
        Args:
            slug: 待校验 slug
            exclude_zone_id: 排除的分区ID（更新场景下排除自身）
        Raises:
            HTTPException: 400 slug 已存在
        """
        existing = forum_zone_crud.get_zone_by_slug(self.db, slug)
        if existing and (exclude_zone_id is None or existing.id != exclude_zone_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分区 slug 已存在",
            )

    def create_zone(
        self, zone_in: ForumZoneCreate, current_user: User
    ) -> ForumZone:
        """
        创建分区（管理员及以上）
        未指定 manager_id 时，默认将当前用户设为区主
        Args:
            zone_in: 分区创建请求
            current_user: 当前登录用户
        Returns:
            ForumZone: 分区对象
        Raises:
            HTTPException: 403 权限不足 / 400 指定的区主不存在或已注销
        """
        self._require_admin(current_user)

        # 若未提供 slug，根据分区名称自动生成
        if not zone_in.slug:
            slug = generate_unique_slug(
                self.db, zone_in.zone_name, exists_checker=forum_zone_crud.get_zone_by_slug
            )
            zone_in = zone_in.model_copy(update={"slug": slug})
        else:
            self._ensure_slug_unique(zone_in.slug)

        # 确定区主：显式指定 > 当前用户
        target_manager_id = (
            zone_in.manager_id if zone_in.manager_id is not None else current_user.id
        )
        self._validate_manager_id(target_manager_id)

        db_zone = forum_zone_crud.create_zone(self.db, zone_in, target_manager_id)
        # 重新查询以加载 manager 关联，避免延迟加载问题
        refreshed = forum_zone_crud.get_zone_by_id(self.db, db_zone.id)
        return refreshed

    def update_zone(
        self, zone_id: int, zone_in: ForumZoneUpdate, current_user: User
    ) -> ForumZone:
        """
        编辑分区（管理员及以上 或 区主）
        区主不能修改 manager_id
        Args:
            zone_id: 分区ID
            zone_in: 分区更新请求
            current_user: 当前登录用户
        Returns:
            ForumZone: 分区对象
        Raises:
            HTTPException: 404 分区不存在 / 403 无权编辑 / 400 slug 已存在 或 区主无权修改 manager_id 或 目标区主不存在/已注销
        """
        db_zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
        if not db_zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )

        is_admin = current_user.permission >= PermissionLevel.ADMIN
        is_manager = is_zone_manager(self.db, db_zone.id, current_user.id)

        if not is_admin and not is_manager:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权编辑此分区"
            )

        update_data = zone_in.model_dump(exclude_unset=True)

        # 仅管理员可修改 manager_id；区主传入则拒绝
        manager_id_changed = False
        if "manager_id" in update_data:
            if not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="区主无权修改 manager_id",
                )
            new_manager_id = update_data["manager_id"]
            if new_manager_id != db_zone.manager_id:
                self._validate_manager_id(new_manager_id)
                manager_id_changed = True

        if "slug" in update_data and update_data["slug"] != db_zone.slug:
            self._ensure_slug_unique(update_data["slug"], exclude_zone_id=db_zone.id)

        filtered_zone_in = ForumZoneUpdate(**update_data)
        updated_zone = forum_zone_crud.update_zone(
            self.db, db_zone, filtered_zone_in
        )

        if manager_id_changed:
            set_zone_manager_cache(updated_zone.id, update_data["manager_id"])

        # 重新查询以加载 manager 关联（可能已变更），避免延迟加载问题
        refreshed = forum_zone_crud.get_zone_by_id(self.db, updated_zone.id)
        return refreshed

    def delete_zone(self, zone_id: int, current_user: User) -> None:
        """
        删除分区（管理员及以上）
        若该分区下还有帖子，将返回 400
        Args:
            zone_id: 分区ID
            current_user: 当前登录用户
        Raises:
            HTTPException: 404 分区不存在 / 400 分区下还有帖子 / 403 权限不足
        """
        self._require_admin(current_user)
        db_zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
        if not db_zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )

        items, total = forum_post_crud.get_posts(
            self.db, zone_id=zone_id, skip=0, limit=1
        )
        if total > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该分区下还有帖子，无法删除",
            )

        forum_zone_crud.delete_zone(self.db, zone_id)
        delete_zone_manager_cache(zone_id)

    def get_zone(self, zone_id: int) -> ForumZone:
        """
        获取分区详情
        Args:
            zone_id: 分区ID
        Returns:
            ForumZone: 分区对象
        Raises:
            HTTPException: 404 分区不存在
        """
        db_zone = forum_zone_crud.get_zone_by_id(self.db, zone_id)
        if not db_zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )
        return db_zone

    def get_zone_by_slug(self, slug: str) -> ForumZone:
        """
        根据 slug 查询分区详情
        Args:
            slug: 分区 slug
        Returns:
            ForumZone: 分区对象
        Raises:
            HTTPException: 404 分区不存在
        """
        db_zone = forum_zone_crud.get_zone_by_slug(self.db, slug)
        if not db_zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="分区不存在"
            )
        return db_zone

    def list_zones(self) -> list[ForumZone]:
        """
        获取所有分区列表
        Returns:
            list[ForumZone]: 分区列表
        """
        return forum_zone_crud.get_all_zones(self.db)
