from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserLoginResponse, UserLogin, UserResponse, UserLogout, UserRegister, UserListResponse, ChangePasswordRequest
from app.models.user import User
from fastapi import HTTPException, status, UploadFile
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token, is_token_blacklisted, blacklist_token
from app.core.config import settings
from app.core.permissions import require_admin
from app.storage.oss import delete_file_from_oss, upload_user_avatar, convert_oss_url_to_file_path

class UserService:

    def __init__(self, db: Session):
        """
        UserService 初始化
        Args:
            db: 数据库会话
        """
        self.db = db

    # ---------- 共用校验方法 ----------

    def _ensure_username_unique(self, username: str, exclude_user_id: int | None = None) -> None:
        """
        校验用户名唯一性
        Args:
            username: 待校验用户名
            exclude_user_id: 排除的用户ID（更新场景下排除自身）
        Raises:
            HTTPException: 用户名已存在
        """
        existing = user_crud.get_user_by_username(self.db, username)
        if existing and (exclude_user_id is None or existing.id != exclude_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

    def _ensure_email_unique(self, email: str, exclude_user_id: int | None = None) -> None:
        """
        校验邮箱唯一性
        Args:
            email: 待校验邮箱
            exclude_user_id: 排除的用户ID（更新场景下排除自身）
        Raises:
            HTTPException: 邮箱已存在
        """
        existing = user_crud.get_user_by_email(self.db, email)
        if existing and (exclude_user_id is None or existing.id != exclude_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    def _require_admin(self, current_user: User) -> None:
        """
        要求当前用户为管理员及以上权限
        """
        require_admin(current_user)

    def _require_owner_or_admin(self, current_user: User, target_user_id: int) -> None:
        """
        要求当前用户为目标用户本人，或管理员及以上权限
        Args:
            current_user: 当前登录用户
            target_user_id: 目标用户ID
        Raises:
            HTTPException: 权限不足
        """
        if current_user.id != target_user_id and current_user.permission < 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

    # ---------- 业务方法 ----------

    def create_user(self, user_in: UserCreate, current_user: User) -> User:
        """
        创建用户（管理员专属）
        Args:
            user_in: 用户创建请求
            current_user: 当前登录用户
        Returns:
            User: 用户对象
        """
        self._require_admin(current_user)
        self._ensure_username_unique(user_in.username)
        self._ensure_email_unique(user_in.email)
        return user_crud.create_user(self.db, user_in)

    def get_user(self, user_id: int, current_user: User) -> User:
        """
        根据用户ID获取用户
        若用户已注销，仅管理员及以上可查看
        """
        user = user_crud.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        if user.is_deleted and current_user.permission < 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户已注销，仅管理员可查看"
            )
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        username: str | None = None,
        email: str | None = None,
        permission: int | None = None,
        current_user: User | None = None,
    ) -> UserListResponse:
        """
        获取用户列表（支持分页与筛选）
        普通用户禁止查询已注销用户
        """
        effective_include_deleted = (
            include_deleted if (current_user and current_user.permission >= 1) else False
        )
        items, total = user_crud.get_users(
            self.db,
            skip=skip,
            limit=limit,
            include_deleted=effective_include_deleted,
            username=username,
            email=email,
            permission=permission,
        )
        return UserListResponse(
            items=[UserResponse.model_validate(user) for user in items],
            total=total,
        )

    async def update_user(self, user_id: int, user_in: UserUpdate, current_user: User, file: UploadFile | None = None) -> UserResponse:
        """
        更新用户
        Args:
            user_id: 用户ID
            user_in: 用户更新请求
            current_user: 当前登录用户
            file: 头像文件
        Returns:
            UserResponse: 用户响应
        """
        self._require_owner_or_admin(current_user, user_id)
        db_user = user_crud.get_user_by_id(self.db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 普通用户禁止修改 permission 字段
        if current_user.permission == 0:
            update_data = user_in.model_dump(exclude_unset=True)
            if "permission" in update_data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权修改权限字段"
                )

        if user_in.username and user_in.username != db_user.username:
            self._ensure_username_unique(user_in.username, exclude_user_id=db_user.id)
        if user_in.email and user_in.email != db_user.email:
            self._ensure_email_unique(user_in.email, exclude_user_id=db_user.id)

        if file:
            # 删除旧头像
            if db_user.avatar_url:
                await delete_file_from_oss(convert_oss_url_to_file_path(db_user.avatar_url))
            # 上传新头像
            avatar_url = await upload_user_avatar(file)
            user_in.avatar_url = avatar_url

        return UserResponse.model_validate(user_crud.update_user(self.db, db_user, user_in))

    def soft_delete_user(self, user_id: int, current_user: User, access_token: str | None = None) -> None:
        """
        逻辑删除用户（注销，管理员或本人）
        注销后会在 Redis 中标记该用户撤销时间，使其所有已签发 token 失效
        """
        self._require_owner_or_admin(current_user, user_id)
        result = user_crud.soft_delete_user(self.db, user_id)
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在或已被注销"
            )

        # 在 Redis 中记录注销时间戳，使该用户所有已有 token 失效
        from app.core.security import blacklist_token_sync
        from app.redis_client import get_sync_redis_client
        import time
        revoked_at = int(time.time())
        redis = get_sync_redis_client()
        ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        redis.setex(f"user_revoked:{user_id}", ttl, revoked_at)

        # 用户自己注销自己时，顺手拉黑当前 token（管理员注销他人不拉黑管理员 token）
        if access_token and current_user.id == user_id:
            blacklist_token_sync(access_token)

    def hard_delete_user(self, user_id: int, current_user: User) -> None:
        """
        硬删除用户（从数据库移除，管理员专属）
        """
        self._require_admin(current_user)
        deleted = user_crud.hard_delete_user(self.db, user_id)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

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
        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已注销"
            )
        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id) if user_login.is_remember else None,
            access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES if user_login.is_remember else None,
            user=UserResponse.model_validate(user)
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

        # Token Rotation：将旧 refresh token 加入黑名单，再签发新令牌
        await blacklist_token(refresh_token)
        return UserLoginResponse(
            token_type="Bearer",
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            access_token_expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            refresh_token_expires_in=settings.REFRESH_TOKEN_EXPIRE_MINUTES,
            user=UserResponse.model_validate(user)
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

    def register_user(self, user_register: UserRegister) -> UserResponse:
        """
        注册用户
        Args:
            user_register: 用户注册请求
        Returns:
            UserResponse: 用户响应
        """
        self._ensure_username_unique(user_register.username)
        self._ensure_email_unique(user_register.email)
        # 强制注册用户的 permission 为 0
        user_data = user_register.model_copy(update={"permission": 0})
        user = user_crud.create_user(self.db, user_data)
        return UserResponse.model_validate(user)

    def change_password(
        self,
        current_user: User,
        password_data: ChangePasswordRequest,
        access_token: str | None = None,
    ) -> None:
        """
        修改当前用户密码
        Args:
            current_user: 当前登录用户
            password_data: 密码修改请求（旧密码 + 新密码）
            access_token: 当前访问令牌（如有则顺手拉黑）
        Raises:
            HTTPException: 旧密码错误 或 新密码与旧密码相同
        """
        if not verify_password(password_data.old_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="旧密码错误"
            )

        if password_data.old_password == password_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新密码不能与旧密码相同"
            )

        current_user.hashed_password = get_password_hash(password_data.new_password)
        self.db.commit()

        # 在 Redis 中记录撤销时间戳，使该用户所有已有 token 失效
        from app.core.security import blacklist_token_sync
        from app.redis_client import get_sync_redis_client
        import time
        revoked_at = int(time.time())
        redis = get_sync_redis_client()
        ttl = settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60
        redis.setex(f"user_revoked:{current_user.id}", ttl, revoked_at)

        # 顺手拉黑当前 token
        if access_token:
            blacklist_token_sync(access_token)
