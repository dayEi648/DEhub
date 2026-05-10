from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import Field

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
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
def get_user(user_id: int, db: Session = Depends(get_db)):
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
def list_users(skip: int = 0, limit: int = Field(default=20, ge=1, le=100), db: Session = Depends(get_db)):
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
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
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
def delete_user(user_id: int, db: Session = Depends(get_db)):
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