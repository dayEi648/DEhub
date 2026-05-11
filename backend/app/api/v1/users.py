from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from fastapi import Query

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserLoginResponse, UserLogin, UserLogout, RefreshTokenRequest
from app.services.user_service import UserService
from app.models.user import User
from app.core.security import get_current_user, get_token_from_header

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    创建用户
    Args:
        user_in: 用户创建请求
        db: 数据库会话
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return service.create_user(user_in)

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    获取用户
    Args:
        user_id: 用户ID
        db: 数据库会话
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return service.get_user(user_id)

@router.get("/", response_model=List[UserResponse])
def list_users(skip: int = 0, limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> List[UserResponse]:
    """
    获取用户列表
    Args:
        skip: 跳过数量
        limit: 限制数量
        db: 数据库会话
    Returns:
        List[UserResponse]: 用户列表
    """
    service = UserService(db)
    return service.list_users(skip, limit)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    更新用户
    Args:
        user_id: 用户ID
        user_in: 用户更新请求
        db: 数据库会话
    Returns:
        UserResponse: 用户响应
    """
    service = UserService(db)
    return service.update_user(user_id, user_in)

@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    """
    删除用户
    Args:
        user_id: 用户ID
        db: 数据库会话
    Returns:
        None
    """
    service = UserService(db)
    service.delete_user(user_id)
    return None

@router.post("/login", response_model=UserLoginResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)) -> UserLoginResponse:
    """
    登录
    Args:
        user_login: 用户登录请求
        db: 数据库会话
    Returns:
        UserLoginResponse: 用户登录响应
    """
    service = UserService(db)
    return service.login_user(user_login)

@router.post("/refresh-token", response_model=UserLoginResponse)
def refresh_access_token(req: RefreshTokenRequest, db: Session = Depends(get_db)) -> UserLoginResponse:
    """
    刷新访问令牌
    Args:
        req: 刷新令牌请求
        db: 数据库会话
    Returns:
        UserLoginResponse: 用户登录响应
    """
    if not req.refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新令牌不能为空")
    service = UserService(db)
    return service.refresh_access_token(req.refresh_token)

@router.post("/logout", status_code=204)
async def logout(
    user_logout: UserLogout,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_token_from_header),
) -> None:
    """
    登出
    Args:
        user_logout: 用户登出请求（可选 refresh_token）
        db: 数据库会话
        current_user: 当前登录用户
        token: 访问令牌（来自 Authorization Header）
    Returns:
        None
    """
    service = UserService(db)
    await service.logout_user(token, user_logout)