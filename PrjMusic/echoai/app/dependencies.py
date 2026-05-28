"""
FastAPI 依赖：JWT 鉴权。
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings

security = HTTPBearer(auto_error=False)


class CurrentUser:
    """当前登录用户信息。"""

    def __init__(self, user_id: int, username: str, role: int, token: str = ""):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.token = token


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> CurrentUser:
    """
    解析 Authorization: Bearer <token>，使用 HS256 验证。
    与 Spring Boot 使用相同的 secret 和算法。
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="缺少 Authorization 头")

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="JWT 已过期")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"无效的 JWT: {e}")

    user_id = payload.get("userId")
    username = payload.get("username")
    role = payload.get("role")

    if user_id is None or username is None or role is None:
        raise HTTPException(status_code=401, detail="JWT 缺少必要字段")

    return CurrentUser(user_id=int(user_id), username=str(username), role=int(role), token=token)


async def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """管理员权限依赖：要求 role >= 2（ADMIN / SUPER_ADMIN）。"""
    if user.role < 2:
        raise HTTPException(status_code=403, detail="仅管理员可操作")
    return user
