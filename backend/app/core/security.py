import bcrypt
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from app.models.user import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.deps import get_db
from sqlalchemy.orm import Session
from app.redis_client import get_redis_client
from typing import Optional
import uuid
from starlette.concurrency import run_in_threadpool


http_bearer = HTTPBearer(auto_error=False)


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer)
) -> str:
    """
    从 Authorization Header 中提取 Bearer Token
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    Args:
        plain_password: 明文密码
        hashed_password: 哈希密码
    Returns:
        bool: 是否验证成功
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    Args:
        password: 明文密码
    Returns:
        str: 哈希密码
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: int) -> str:
    """
    创建访问令牌
    Args:
        user_id: 用户ID
    Returns:
        str: 访问令牌
    """
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(user_id), "exp": int(expire.timestamp()), "jti": jti, "type": "access", "iat": int(now.timestamp())}
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(user_id: int) -> str:
    """
    创建刷新令牌
    Args:
        user_id: 用户ID
    Returns:
        str: 刷新令牌
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())
    to_encode = {"sub": str(user_id), "exp": int(expire.timestamp()), "jti": jti, "type": "refresh", "iat": int(now.timestamp())}
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def decode_token(token: str) -> dict | None:
    """
    解码JWT令牌
    Args:
        token: JWT令牌
    Returns:
        dict | None: 解码后的载荷，失败返回None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> User:
    """
    根据令牌获取当前用户, 保护路由时使用
    Args:
        token: 访问令牌
    Returns:
        User: 当前用户
    """
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败", headers={"WWW-Authenticate": "Bearer"})

    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌类型错误", headers={"WWW-Authenticate": "Bearer"})

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已注销", headers={"WWW-Authenticate": "Bearer"})

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")

    from app.crud import user as user_crud
    user = await run_in_threadpool(user_crud.get_user_by_id, db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    # 检查用户是否已被注销（用户级 token 撤销）
    redis = get_redis_client()
    revoked_at_str = await redis.get(f"user_revoked:{user_id}")
    if revoked_at_str:
        iat = payload.get("iat")
        if iat and float(iat) < float(revoked_at_str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已注销",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user
    
async def blacklist_token(access_token: str, refresh_token: Optional[str] = None) -> None:
    """
    将所有令牌加入黑名单
    TTL 设为该 token 的剩余存活时间
    Args:
        refresh_token: 刷新令牌
        access_token: 访问令牌
    Returns:
        None
    """
    payload_access_token = decode_token(access_token)
    payload_refresh_token = decode_token(refresh_token) if refresh_token else None
    sub_access = payload_access_token.get("sub") if payload_access_token else None
    jti_access = payload_access_token.get("jti") if payload_access_token else None
    exp_access = payload_access_token.get("exp") if payload_access_token else None
    sub_refresh = payload_refresh_token.get("sub") if payload_refresh_token else None
    jti_refresh = payload_refresh_token.get("jti") if payload_refresh_token else None
    exp_refresh = payload_refresh_token.get("exp") if payload_refresh_token else None

    if sub_refresh and jti_refresh and exp_refresh:
        ttl = int(exp_refresh) - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            redis = get_redis_client()
            await redis.setex(f"jwt_blacklist:{jti_refresh}", ttl, "revoked")
    if sub_access and jti_access and exp_access:
        ttl = int(exp_access) - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            redis = get_redis_client()
            await redis.setex(f"jwt_blacklist:{jti_access}", ttl, "revoked")

async def is_token_blacklisted(jti: str) -> bool:
    """
    检查令牌是否在黑名单中
    Args:
        jti: 令牌ID
    Returns:
        bool: 是否在黑名单中
    """
    redis = get_redis_client()
    return await redis.exists(f"jwt_blacklist:{jti}") > 0

