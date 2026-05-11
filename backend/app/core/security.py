import bcrypt
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.crud import user as user_crud
from app.schemas.user import UserResponse
from fastapi.security import OAuth2PasswordBearer
from app.api.deps import get_db
from sqlalchemy.orm import Session
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")




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


def create_access_token(user_id: int, email: str) -> str:
    """
    创建访问令牌
    Args:
        user_id: 用户ID
        email: 邮箱
        expires_delta: 过期时间
    Returns:
        str: 访问令牌
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def create_refresh_token(user_id: int, email: str) -> str:
    """
    创建刷新令牌
    Args:
        user_id: 用户ID
        email: 邮箱
    Returns:
        str: 刷新令牌
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def decode_access_token(token: str) -> dict | None:
    """
    解码访问令牌
    Args:
        token: 访问令牌
    Returns:
        dict | None: 解码后的令牌
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # 解码失败,返回None
        return None

def decode_refresh_token(token: str) -> dict | None:
    """
    解码刷新令牌
    Args:
        token: 刷新令牌
    Returns:
        dict | None: 解码后的令牌
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # 解码失败，表示Token 过期
        return None

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    根据令牌获取当前用户, 保护路由时使用
    Args:
        token: 访问令牌
    Returns:
        User: 当前用户
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")

    user = user_crud.get_user_by_email(db, email) or user_crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    return user
    
