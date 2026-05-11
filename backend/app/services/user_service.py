from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserLoginResponse, UserLogin, UserResponse
from app.models.user import User
from fastapi import HTTPException, status
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.core.config import settings
class UserService:

    
    def __init__(self, db: Session):
        """
        UserService 初始化
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def create_user(self, user_in: UserCreate) -> User:
        """
        创建用户
        Args:
            user_in: 用户创建请求
        Returns:
            User: 用户对象
        """
        # 业务校验：用户名唯一性
        if user_crud.get_user_by_username(self.db, user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        # 邮箱唯一性校验
        if user_crud.get_user_by_email(self.db, user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )
        # 创建用户
        return user_crud.create_user(self.db, user_in)
    
    def get_user(self, user_id: int) -> User:
        """
        根据用户ID获取用户
        Args:
            user_id: 用户ID
        Returns:
            User: 用户对象
        """
        user = user_crud.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
    
    def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """
        获取用户列表
        Args:
            skip: 跳过数量
            limit: 限制数量
        Returns:
            list[User]: 用户列表
        """
        return user_crud.get_users(self.db, skip=skip, limit=limit)
    
    def update_user(self, user_id: int, user_in: UserUpdate) -> User:
        """
        更新用户
        Args:
            user_id: 用户ID
            user_in: 用户更新请求
        Returns:
            User: 用户对象
        """
        # 确认用户存在
        db_user = self.get_user(user_id)

        # 业务校验：用户名唯一性
        if user_in.username and user_in.username != db_user.username:
            if user_crud.get_user_by_username(self.db, user_in.username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
        # 邮箱唯一性校验
        if user_in.email and user_in.email != db_user.email:
            if user_crud.get_user_by_email(self.db, user_in.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱已存在"
                )
        # 更新用户
        return user_crud.update_user(self.db, db_user, user_in)

    def delete_user(self, user_id: int) -> None:
        """
        删除用户
        Args:
            user_id: 用户ID
        Returns:
            None
        """
        deleted = user_crud.delete_user(self.db, user_id)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return None

    def authenticate_user(self, user_login: UserLogin) -> User | None:
        """
        验证用户
        Args:
            user_login: 用户登录请求
        Returns:
            User | None: 用户对象或None
        """
        user = user_crud.get_user_by_email(self.db, user_login.account) or user_crud.get_user_by_username(self.db, user_login.account)
        if not user:
            return None
        if not verify_password(user_login.password, user.hashed_password):
            return None
        return user
    
    def login_user(self, user_login: UserLogin) -> UserLoginResponse:
        """
        登录
        Args:
            user_login: 用户登录请求
        Returns:
            UserLoginResponse: 用户登录响应
        """
        user = self.authenticate_user(user_login)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或密码错误"   
            )
        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(user.id, user.email),
            refresh_token=create_refresh_token(user.id, user.email),
            access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            )
        )