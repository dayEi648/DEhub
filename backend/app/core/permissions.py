from fastapi import HTTPException, status
from app.models.user import User


def require_super_admin(current_user: User) -> None:
    """要求当前用户为超级管理员"""
    if current_user.permission != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足，需要超级管理员权限",
        )


def require_admin(current_user: User) -> None:
    """要求当前用户为管理员及以上"""
    if current_user.permission < 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足",
        )
