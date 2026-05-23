from fastapi import HTTPException, status
from app.models.user import User
from app.core.permission_levels import PermissionLevel


def require_super_admin(current_user: User) -> None:
    """要求当前用户为超级管理员"""
    if current_user.permission != PermissionLevel.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级管理员权限",
        )


def require_admin(current_user: User) -> None:
    """要求当前用户为管理员及以上"""
    if current_user.permission < PermissionLevel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )


def require_owner_or_admin(current_user: User, owner_user_id: int) -> None:
    """要求当前用户为资源所有者本人，或管理员及以上。"""
    if current_user.id != owner_user_id and current_user.permission < PermissionLevel.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
