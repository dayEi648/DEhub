import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.user_service import UserService
from app.schemas.user import ChangePasswordRequest


class TestChangePassword:
    """测试修改密码业务逻辑"""

    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return UserService(db)

    @pytest.fixture
    def current_user(self):
        user = MagicMock()
        user.id = 1
        user.hashed_password = "hashed_old_password"
        return user

    def test_change_password_success(self, service, current_user):
        """旧密码正确且新密码不同，应成功修改密码并触发 Token 失效"""
        password_data = ChangePasswordRequest(
            old_password="oldpass123",
            new_password="newpass123",
        )

        with patch(
            "app.services.user_service.verify_password", return_value=True
        ) as mock_verify, patch(
            "app.services.user_service.get_password_hash", return_value="hashed_new_password"
        ) as mock_hash, patch(
            "app.redis_client.get_sync_redis_client"
        ) as mock_get_redis:
            mock_redis = MagicMock()
            mock_get_redis.return_value = mock_redis

            service.change_password(current_user, password_data)

            mock_verify.assert_called_once_with("oldpass123", "hashed_old_password")
            mock_hash.assert_called_once_with("newpass123")
            assert current_user.hashed_password == "hashed_new_password"
            service.db.commit.assert_called_once()
            mock_get_redis.assert_called_once()
            mock_redis.set.assert_called_once()
            # 验证 Redis key 格式
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "user_revoked:1"

    def test_change_password_wrong_old_password(self, service, current_user):
        """旧密码错误，应抛出 401"""
        password_data = ChangePasswordRequest(
            old_password="wrongpass123",
            new_password="newpass123",
        )

        with patch(
            "app.services.user_service.verify_password", return_value=False
        ) as mock_verify, patch(
            "app.core.security.get_password_hash"
        ) as mock_hash:
            with pytest.raises(HTTPException) as exc_info:
                service.change_password(current_user, password_data)

            assert exc_info.value.status_code == 401
            assert "旧密码错误" in exc_info.value.detail
            mock_verify.assert_called_once_with("wrongpass123", "hashed_old_password")
            mock_hash.assert_not_called()
            service.db.commit.assert_not_called()

    def test_change_password_same_as_old(self, service, current_user):
        """新密码与旧密码相同，应抛出 400"""
        # 使用 model_construct 绕过 Pydantic 校验，测试 Service 层兜底逻辑
        password_data = ChangePasswordRequest.model_construct(
            old_password="samepass123",
            new_password="samepass123",
        )

        with patch(
            "app.services.user_service.verify_password", return_value=True
        ) as mock_verify, patch(
            "app.core.security.get_password_hash"
        ) as mock_hash:
            with pytest.raises(HTTPException) as exc_info:
                service.change_password(current_user, password_data)

            assert exc_info.value.status_code == 400
            assert "新密码不能与旧密码相同" in exc_info.value.detail
            mock_verify.assert_called_once_with("samepass123", "hashed_old_password")
            mock_hash.assert_not_called()
            service.db.commit.assert_not_called()
