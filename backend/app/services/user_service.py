from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserLoginResponse, UserLogin, UserResponse, UserLogout
from app.models.user import User
from fastapi import HTTPException, status
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token, is_token_blacklisted, blacklist_token
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

    # 预生成一个无效的 bcrypt hash，用于时序攻击防护（dummy check）
    _DUMMY_HASH = "$2b$12$4LPTZltcFxdjkL4ONdOM0OQnYxLfYQvH3h1xWJQu7e1KqCb0XvC7e"

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
            # 执行 dummy verify 以掩藏"用户不存在"与"密码错误"的时序差异
            verify_password(user_login.password, self._DUMMY_HASH)
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
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id) if user_login.is_remember else None,
            access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES if user_login.is_remember else None,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            )
        )

    async def refresh_access_token(self, refresh_token: str) -> UserLoginResponse:
        """
        刷新令牌
        刷新后将旧 refresh token 加入黑名单（Token Rotation）
        Args:
            refresh_token: 刷新令牌
        Returns:
            UserLoginResponse: 用户登录响应
        """
        payload = decode_token(refresh_token)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")
        token_type = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌类型错误")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")
        user = user_crud.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
        jti_refresh = payload.get("jti")
        if jti_refresh and await is_token_blacklisted(jti_refresh):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已注销")
        # Token Rotation：将旧 refresh token 加入黑名单，再签发新令牌
        await blacklist_token(refresh_token)
        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            user=UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                created_at=user.created_at
            )
        )

    async def logout_user(self, access_token: str, user_logout: UserLogout) -> None:
        """
        登出
        1. 将 access_token 加入黑名单。
        2. 如果 Body 里带了 refresh_token（记住登录场景），也加入黑名单。
        Args:
            access_token: 访问令牌（来自 Header）
            user_logout: 用户登出请求（可选 refresh_token）
        Returns:
            None
        """
        await blacklist_token(access_token, user_logout.refresh_token if user_logout.refresh_token else None)