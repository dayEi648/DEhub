import logging

from sqlalchemy.orm import Session
from app.crud import user as user_crud
from app.crud import forum_zone as forum_zone_crud
from app.crud import forum_post as forum_post_crud
from app.crud import forum_reply as forum_reply_crud
from app.crud import comment as comment_crud
from app.crud import ai_conversation as ai_conversation_crud
from app.crud import user_favorite as user_favorite_crud
from app.schemas.user import UserCreate, UserUpdate, UserLogin, UserLogout, UserRegister, ChangePasswordRequest
from app.models.user import User
from fastapi import HTTPException, status, UploadFile
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    decode_token, is_token_blacklisted, blacklist_token, revoke_user_tokens,
)
from app.core.config import settings
from app.core.permissions import require_admin, require_owner_or_admin
from app.core.permission_levels import PermissionLevel
from app.storage.oss import upload_image, ImageUploadScene, convert_oss_url_to_file_path
from app.services.oss_cleanup_service import OssCleanupService
from app.redis_client import get_redis_client, get_sync_redis_client
from app.infrastructure.checkpoint_client import delete_checkpoint_sync
from app.infrastructure.cache_invalidator import ForumCacheInvalidator, BlogCacheInvalidator

logger = logging.getLogger(__name__)


class UserService:
    _CONVERSATION_BATCH_SIZE = 100

    def __init__(self, db: Session):
        self.db = db

    # ---------- 共用校验方法 ----------

    def _ensure_username_unique(self, username: str, exclude_user_id: int | None = None) -> None:
        existing = user_crud.get_user_by_username(self.db, username)
        if existing and (exclude_user_id is None or existing.id != exclude_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )

    def _ensure_email_unique(self, email: str, exclude_user_id: int | None = None) -> None:
        existing = user_crud.get_user_by_email(self.db, email)
        if existing and (exclude_user_id is None or existing.id != exclude_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已存在"
            )

    # ---------- 业务方法 ----------

    def create_user(self, user_in: UserCreate, current_user: User) -> User:
        """创建用户（管理员专属）。管理员不能创建超级管理员。"""
        require_admin(current_user)

        if current_user.permission == PermissionLevel.ADMIN and user_in.permission == PermissionLevel.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足，管理员无法创建超级管理员"
            )

        self._ensure_username_unique(user_in.username)
        self._ensure_email_unique(user_in.email)
        return user_crud.create_user(self.db, user_in)

    def get_user(self, user_id: int, current_user: User) -> User:
        """根据用户ID获取用户。若用户已注销，仅管理员及以上可查看。"""
        user = user_crud.get_user_by_id(self.db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        if user.is_deleted and current_user.permission < PermissionLevel.ADMIN:
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
    ) -> tuple[list[User], int]:
        """获取用户列表（支持分页与筛选）。管理员及以上可查询。"""
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证",
            )
        require_admin(current_user)
        items, total = user_crud.get_users(
            self.db,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted,
            username=username,
            email=email,
            permission=permission,
        )
        return items, total

    async def update_user(self, user_id: int, user_in: UserUpdate, current_user: User, file: UploadFile | None = None) -> User:
        """更新用户（本人或管理员）。"""
        db_user = user_crud.get_user_by_id(self.db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        require_owner_or_admin(current_user, user_id)
        if db_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已注销，无法修改资料"
            )

        # 普通用户禁止修改 permission 字段；管理员禁止将用户提升为超级管理员
        update_data = user_in.model_dump(exclude_unset=True)
        if "permission" in update_data:
            if current_user.permission == PermissionLevel.USER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权修改权限字段"
                )
            if (
                current_user.permission == PermissionLevel.ADMIN
                and update_data["permission"] == PermissionLevel.SUPER_ADMIN
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足，管理员无法将用户提升为超级管理员"
                )

        if user_in.username and user_in.username != db_user.username:
            self._ensure_username_unique(user_in.username, exclude_user_id=db_user.id)
        if user_in.email and user_in.email != db_user.email:
            self._ensure_email_unique(user_in.email, exclude_user_id=db_user.id)

        old_avatar_url = db_user.avatar_url
        new_avatar_url: str | None = None
        cleanup_service = OssCleanupService()
        if file:
            new_avatar_url = await upload_image(file, ImageUploadScene.avatar)
            db_user.avatar_url = new_avatar_url

        try:
            updated = user_crud.update_user(self.db, db_user, user_in)
        except Exception:
            self.db.rollback()
            if new_avatar_url:
                await cleanup_service.delete_file_after_commit(
                    convert_oss_url_to_file_path(new_avatar_url),
                    source="user.avatar.rollback",
                )
            db_user.avatar_url = old_avatar_url
            raise

        if new_avatar_url and old_avatar_url:
            await cleanup_service.delete_file_after_commit(
                convert_oss_url_to_file_path(old_avatar_url),
                source="user.avatar",
            )

        return updated

    def soft_delete_user(self, user_id: int, current_user: User, access_token: str | None = None) -> None:
        """逻辑删除用户（注销，管理员或本人）。注销后所有已签发 token 失效。"""
        require_owner_or_admin(current_user, user_id)
        result = user_crud.soft_delete_user(self.db, user_id)
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在或已被注销"
            )

        # 用户自己注销自己时，顺手拉黑当前 token（管理员注销他人不拉黑管理员 token）
        if access_token and current_user.id == user_id:
            revoke_user_tokens(user_id, access_token)
        else:
            revoke_user_tokens(user_id)

    def hard_delete_user(self, user_id: int, current_user: User) -> None:
        """硬删除用户（管理员专属）。级联清理头像、分区、对话、评论、帖子、收藏等。"""
        require_admin(current_user)
        avatar_url_for_cleanup: str | None = None
        checkpoint_conversation_ids: list[int] = []

        try:
            with self.db.begin():
                db_user = user_crud.get_user_by_id(self.db, user_id)
                if not db_user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="用户不存在"
                    )
                avatar_url_for_cleanup = db_user.avatar_url

                # 转移区主身份
                forum_zone_crud.update_zones_manager_by_old_manager(
                    self.db, user_id, current_user.id, auto_commit=False
                )

                # 删除 AI 对话（分批处理避免一次性拉取大量数据）
                while True:
                    convs, _total = ai_conversation_crud.list_ai_conversations_by_user(
                        self.db, user_id, skip=0, limit=self._CONVERSATION_BATCH_SIZE
                    )
                    if not convs:
                        break

                    for conv in convs:
                        checkpoint_conversation_ids.append(conv.id)
                        ai_conversation_crud.delete_ai_conversation(
                            self.db, conv.id, auto_commit=False
                        )

                # 删除评论及子评论
                user_comment_ids = comment_crud.get_comment_ids_by_user_id(
                    self.db, user_id
                )
                child_comment_ids = comment_crud.get_child_comment_ids_by_parent_ids(
                    self.db, user_comment_ids
                )
                all_comment_ids = list(set(user_comment_ids + child_comment_ids))
                if all_comment_ids:
                    comment_crud.delete_comment_likes_by_comment_ids(
                        self.db, all_comment_ids, auto_commit=False
                    )
                    comment_crud.delete_comments_by_ids(
                        self.db, all_comment_ids, auto_commit=False
                    )

                # 删除论坛帖子和回复
                user_post_ids = forum_post_crud.get_post_ids_by_user_id(
                    self.db, user_id
                )
                if user_post_ids:
                    forum_reply_crud.delete_replies_by_post_ids(
                        self.db, user_post_ids, auto_commit=False
                    )
                    for post_id in user_post_ids:
                        forum_post_crud.delete_post(
                            self.db, post_id, auto_commit=False
                        )
                forum_reply_crud.delete_replies_by_user_id(
                    self.db, user_id, auto_commit=False
                )
                forum_reply_crud.delete_forum_reply_likes_by_user_id(
                    self.db, user_id, auto_commit=False
                )

                # 删除收藏/点赞/关注记录
                user_favorite_crud.delete_all_favorites_by_user_id(
                    self.db, user_id, auto_commit=False
                )

                # 最后删除用户
                deleted = user_crud.hard_delete_user(
                    self.db, user_id, auto_commit=False
                )
                if deleted == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="用户不存在"
                    )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("硬删除关键清理步骤失败: user=%s", user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="关键清理步骤失败，已中止用户硬删除",
            ) from exc

        # 事务提交成功后统一失效相关缓存
        BlogCacheInvalidator.invalidate_blog_posts()
        ForumCacheInvalidator.invalidate_forum_posts()
        ForumCacheInvalidator.invalidate_forum_zones()

        # 删除用户头像
        if avatar_url_for_cleanup:
            OssCleanupService().delete_file_after_commit_sync(
                convert_oss_url_to_file_path(avatar_url_for_cleanup),
                source="user.avatar.hard_delete",
            )

        # 清理 Redis checkpoint
        for conv_id in checkpoint_conversation_ids:
            try:
                delete_checkpoint_sync(str(conv_id))
            except Exception:
                logger.exception("清理 AI 对话 checkpoint 失败: conv=%s", conv_id)

        # 清理 Redis 撤销标记
        try:
            redis = get_sync_redis_client()
            redis.delete(f"user_revoked:{user_id}")
        except Exception:
            logger.exception("清理 Redis 撤销标记失败: user=%s", user_id)

    # 预生成一个无效的 bcrypt hash，用于时序攻击防护（dummy check）
    _DUMMY_HASH = "$2b$12$4LPTZltcFxdjkL4ONdOM0OQnYxLfYQvH3h1xWJQu7e1KqCb0XvC7e"

    def authenticate_user(self, user_login: UserLogin) -> User | None:
        """验证用户密码。"""
        account = user_login.account
        user = user_crud.get_user_by_username(self.db, account)
        if user is None:
            user = user_crud.get_user_by_email(self.db, account)
        if not user:
            verify_password(user_login.password, self._DUMMY_HASH)
            return None
        if not verify_password(user_login.password, user.hashed_password):
            return None
        return user

    def login_user(self, user_login: UserLogin) -> tuple[User, str, str | None]:
        """登录。返回 (用户, access_token, refresh_token)。"""
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
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id) if user_login.is_remember else None
        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> tuple[User, str, str]:
        """刷新令牌（Token Rotation：旧 refresh token 加入黑名单）。"""
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
            try:
                revoked_at = float(revoked_at_str)
                issued_at = float(iat) if iat is not None else None
            except (ValueError, TypeError):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌校验失败")
            if issued_at is not None and issued_at < revoked_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户已注销",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # Token Rotation
        await blacklist_token(refresh_token)
        access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        return user, access_token, new_refresh_token

    async def logout_user(self, access_token: str, user_logout: UserLogout) -> None:
        """登出：将 access_token（及可选 refresh_token）加入黑名单。"""
        await blacklist_token(access_token, user_logout.refresh_token if user_logout.refresh_token else None)

    def register_user(self, user_register: UserRegister) -> User:
        """注册用户（强制 permission 为 0）。"""
        self._ensure_username_unique(user_register.username)
        self._ensure_email_unique(user_register.email)
        user_data = UserCreate.model_validate(
            user_register.model_copy(update={"permission": PermissionLevel.USER}).model_dump()
        )
        return user_crud.create_user(self.db, user_data)

    def change_password(
        self,
        current_user: User,
        password_data: ChangePasswordRequest,
        access_token: str | None = None,
    ) -> None:
        """修改当前用户密码。成功后使该用户所有已有 token 失效。"""
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

        # 使该用户所有已有 token 失效
        revoke_user_tokens(current_user.id, access_token)
