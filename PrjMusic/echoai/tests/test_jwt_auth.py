"""
测试 JWT 鉴权功能。
"""
import time
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import FastAPI, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.testclient import TestClient

from app.dependencies import get_current_user, CurrentUser
from app.config import settings

# 创建临时应用用于测试
app = FastAPI()
security = HTTPBearer()


@app.get("/protected")
async def protected_route(user: CurrentUser = Depends(get_current_user)):
    return {
        "code": 200,
        "msg": "ok",
        "data": {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
        },
    }


client = TestClient(app)


def make_token(user_id: int, username: str, role: int, exp_delta_seconds: int = 3600) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "userId": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=exp_delta_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def test_valid_token():
    token = make_token(1, "testuser", 0)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["user_id"] == 1
    assert data["data"]["username"] == "testuser"
    assert data["data"]["role"] == 0
    print("[PASS] 有效 JWT 测试通过")


def test_expired_token():
    token = make_token(1, "testuser", 0, exp_delta_seconds=-1)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    print("[PASS] 过期 JWT 测试通过")


def test_invalid_token():
    resp = client.get("/protected", headers={"Authorization": "Bearer invalid_token"})
    assert resp.status_code == 401
    print("[PASS] 无效 JWT 测试通过")


def test_missing_token():
    resp = client.get("/protected")
    assert resp.status_code == 401
    print("[PASS] 缺少 JWT 测试通过")


def test_wrong_secret():
    payload = {
        "userId": 1,
        "username": "testuser",
        "role": 0,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    print("[PASS] 错误 Secret JWT 测试通过")


if __name__ == "__main__":
    test_valid_token()
    test_expired_token()
    test_invalid_token()
    test_missing_token()
    test_wrong_secret()
    print("\n[OK] 所有 JWT 鉴权测试通过！")
