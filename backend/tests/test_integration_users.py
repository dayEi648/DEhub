"""Users 模块集成测试。"""

import pytest

from app.core.security import get_current_user
from app.main import app


class TestUserRegister:
    def test_register_user_success(self, client):
        """正常注册用户应返回 201 及用户基本信息。"""
        payload = {
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "123456",
        }
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newbie"
        assert data["email"] == "newbie@example.com"
        assert "id" in data
        assert data["permission"] == 0

    def test_register_duplicate_username_should_fail(self, client, normal_user):
        """重复用户名应返回 400。"""
        payload = {
            "username": normal_user.username,
            "email": "another@example.com",
            "password": "123456",
        }
        response = client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 400


class TestUserLogin:
    def test_login_with_valid_credentials(self, client, normal_user):
        """使用正确密码登录应返回 access_token。"""
        # normal_user 的密码是 dummy hash，无法通过真实校验。
        # 这里我们直接创建一个带真实哈希密码的用户。
        from app.core.security import get_password_hash
        from app.models.user import User

        user = User(
            username="logintest",
            email="login@test.com",
            hashed_password=get_password_hash("secret123"),
            permission=0,
        )
        # 通过 db_session 创建用户需要 fixture，这里简化为直接调用注册接口
        client.post("/api/v1/users/register", json={
            "username": "logintest",
            "email": "login@test.com",
            "password": "secret123",
        })

        response = client.post("/api/v1/users/login", json={
            "account": "logintest",
            "password": "secret123",
            "is_remember": False,
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_with_invalid_password_should_fail(self, client):
        """错误密码应返回 401。"""
        response = client.post("/api/v1/users/login", json={
            "account": "notexist",
            "password": "wrongpwd",
            "is_remember": False,
        })
        assert response.status_code == 401


class TestUserAdminOperations:
    def test_admin_create_user(self, auth_client):
        """管理员创建用户应返回 201。"""
        payload = {
            "username": "created_by_admin",
            "email": "cba@test.com",
            "password": "123456",
            "permission": 0,
        }
        response = auth_client.post("/api/v1/users/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "created_by_admin"

    def test_list_users(self, auth_client, normal_user):
        """获取用户列表应包含已有用户。"""
        response = auth_client.get("/api/v1/users/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        usernames = [u["username"] for u in data["items"]]
        assert normal_user.username in usernames

    def test_normal_user_cannot_list_users(self, client, normal_user):
        """普通登录用户不能枚举用户列表。"""
        async def override_get_current_user():
            return normal_user

        app.dependency_overrides[get_current_user] = override_get_current_user
        response = client.get("/api/v1/users/")

        assert response.status_code == 403
