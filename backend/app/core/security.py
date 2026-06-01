import bcrypt
import time
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, status
from app.models.user import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.deps import get_db
from sqlalchemy.orm import Session
from app.redis_client import get_redis_client, get_sync_redis_client
import uuid
from starlette.concurrency import run_in_threadpool


http_bearer = HTTPBearer(auto_error=False)


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer)
) -> str:
    """从 Authorization Header 中提取 Bearer Token。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: int) -> str:
    """创建访问令牌。"""
    return _create_token(user_id, "access", settings.ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌。"""
    return _create_token(user_id, "refresh", settings.REFRESH_TOKEN_EXPIRE_MINUTES)


def _create_token(user_id: int, token_type: str, expire_minutes: int) -> str:
    """创建指定类型和过期时间的 JWT。"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expire_minutes)
    jti = str(uuid.uuid4())
    to_encode = {
        "sub": str(user_id),
        "exp": int(expire.timestamp()),
        "jti": jti,
        "type": token_type,
        "iat": int(now.timestamp()),
    }
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    """解码 JWT 令牌，失败返回 None。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(request: Request, token: str = Depends(get_token_from_header), db: Session = Depends(get_db)) -> User:
    """根据令牌获取当前用户，用于保护路由。"""
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败", headers={"WWW-Authenticate": "Bearer"})
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败", headers={"WWW-Authenticate": "Bearer"})

    from app.crud import user as user_crud
    user = await run_in_threadpool(user_crud.get_user_by_id, db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在", headers={"WWW-Authenticate": "Bearer"})

    # 检查用户是否已被注销（用户级 token 撤销）
    redis = get_redis_client()
    revoked_at_str = await redis.get(f"user_revoked:{user_id}")
    if revoked_at_str:
        iat = payload.get("iat")
        try:
            revoked_at = float(revoked_at_str)
            issued_at = float(iat) if iat is not None else None
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌校验失败",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if issued_at is not None and issued_at < revoked_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已注销",
                headers={"WWW-Authenticate": "Bearer"},
            )

    request.state.user = user
    return user


async def blacklist_token(access_token: str, refresh_token: str | None = None) -> None:
    """将所有令牌加入黑名单（TTL 设为剩余存活时间）。"""
    redis = get_redis_client()
    for jti, ttl in _iter_revocable_entries(access_token, refresh_token):
        await redis.setex(f"jwt_blacklist:{jti}", ttl, "revoked")


def blacklist_token_sync(access_token: str, refresh_token: str | None = None) -> None:
    """同步版本：将令牌加入黑名单。"""
    redis = get_sync_redis_client()
    for jti, ttl in _iter_revocable_entries(access_token, refresh_token):
        redis.setex(f"jwt_blacklist:{jti}", ttl, "revoked")


def revoke_user_tokens(user_id: int, access_token: str | None = None) -> None:
    """在 Redis 中标记用户撤销时间，使其所有已签发 token 失效。"""
    try:
        revoked_at = int(time.time())
        ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        get_sync_redis_client().setex(f"user_revoked:{user_id}", ttl, revoked_at)
        if access_token:
            blacklist_token_sync(access_token)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Token 失效标记失败: user=%s", user_id)


def _iter_revocable_entries(
    access_token: str,
    refresh_token: str | None = None,
) -> list[tuple[str, int]]:
    """提取需要写入黑名单的 (jti, ttl) 列表。"""
    entries: list[tuple[str, int]] = []
    now_ts = int(datetime.now(timezone.utc).timestamp())
    for token in (refresh_token, access_token):
        if not token:
            continue
        payload = decode_token(token)
        if payload is None:
            continue
        jti = payload.get("jti")
        exp = payload.get("exp")
        if not jti or exp is None:
            continue
        ttl = int(exp) - now_ts
        if ttl > 0:
            entries.append((jti, ttl))
    return entries


async def is_token_blacklisted(jti: str) -> bool:
    """检查令牌是否在黑名单中。"""
    redis = get_redis_client()
    return await redis.exists(f"jwt_blacklist:{jti}") > 0
