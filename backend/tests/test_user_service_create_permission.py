"""UserService.create_user 权限限制单元测试。

验证：管理员(permission=1)无法创建超管(permission=2)，
      超管(permission=2)可以创建任意权限级别的用户。
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.permission_levels import PermissionLevel
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class TestCreateUserPermissionLimit:
    """测试创建用户时的权限上限限制。"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserService(mock_db)

    @pytest.fixture
    def admin_user(self):
        user = MagicMock()
        user.id = 10
        user.permission = PermissionLevel.ADMIN
        return user

    @pytest.fixture
    def super_admin_user(self):
        user = MagicMock()
        user.id = 20
        user.permission = PermissionLevel.SUPER_ADMIN
        return user

    def _make_user_create(self, permission: int) -> UserCreate:
        return UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            permission=permission,
        )

    @patch("app.services.user_service.user_crud")
    @patch.object(UserService, "_ensure_username_unique")
    @patch.object(UserService, "_ensure_email_unique")
    def test_admin_create_user_success(
        self,
        mock_ensure_email,
        mock_ensure_username,
        mock_user_crud,
        service,
        admin_user,
    ):
        """管理员创建普通用户，应成功。"""
        user_in = self._make_user_create(PermissionLevel.USER)
        mock_user_crud.create_user.return_value = MagicMock()

        result = service.create_user(user_in, admin_user)

        assert result is not None
        mock_user_crud.create_user.assert_called_once()

    @patch("app.services.user_service.user_crud")
    @patch.object(UserService, "_ensure_username_unique")
    @patch.object(UserService, "_ensure_email_unique")
    def test_admin_create_admin_success(
        self,
        mock_ensure_email,
        mock_ensure_username,
        mock_user_crud,
        service,
        admin_user,
    ):
        """管理员创建管理员，应成功。"""
        user_in = self._make_user_create(PermissionLevel.ADMIN)
        mock_user_crud.create_user.return_value = MagicMock()

        result = service.create_user(user_in, admin_user)

        assert result is not None
        mock_user_crud.create_user.assert_called_once()

    @patch("app.services.user_service.user_crud")
    @patch.object(UserService, "_ensure_username_unique")
    @patch.object(UserService, "_ensure_email_unique")
    def test_admin_create_super_admin_forbidden(
        self,
        mock_ensure_email,
        mock_ensure_username,
        mock_user_crud,
        service,
        admin_user,
    ):
        """管理员创建超级管理员，应返回 403。"""
        user_in = self._make_user_create(PermissionLevel.SUPER_ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            service.create_user(user_in, admin_user)

        assert exc_info.value.status_code == 403
        assert "管理员无法创建超级管理员" in exc_info.value.detail
        mock_user_crud.create_user.assert_not_called()

    @patch("app.services.user_service.user_crud")
    @patch.object(UserService, "_ensure_username_unique")
    @patch.object(UserService, "_ensure_email_unique")
    def test_super_admin_create_super_admin_success(
        self,
        mock_ensure_email,
        mock_ensure_username,
        mock_user_crud,
        service,
        super_admin_user,
    ):
        """超级管理员创建超级管理员，应成功。"""
        user_in = self._make_user_create(PermissionLevel.SUPER_ADMIN)
        mock_user_crud.create_user.return_value = MagicMock()

        result = service.create_user(user_in, super_admin_user)

        assert result is not None
        mock_user_crud.create_user.assert_called_once()
