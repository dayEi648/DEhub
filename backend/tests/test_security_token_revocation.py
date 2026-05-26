from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.security import get_current_user
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_revoked_at_without_500():
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value="not-a-timestamp")

    with (
        patch("app.core.security.decode_token") as mock_decode,
        patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock) as mock_blacklisted,
        patch("app.core.security.get_redis_client", return_value=redis),
        patch("app.crud.user.get_user_by_id") as mock_get_user,
    ):
        mock_decode.return_value = {
            "type": "access",
            "jti": "token-id",
            "sub": "1",
            "iat": 100,
        }
        mock_blacklisted.return_value = False
        mock_get_user.return_value = MagicMock(id=1)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="token", db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "令牌校验失败"


@pytest.mark.asyncio
async def test_get_current_user_rejects_invalid_iat_without_500():
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value="200")

    with (
        patch("app.core.security.decode_token") as mock_decode,
        patch("app.core.security.is_token_blacklisted", new_callable=AsyncMock) as mock_blacklisted,
        patch("app.core.security.get_redis_client", return_value=redis),
        patch("app.crud.user.get_user_by_id") as mock_get_user,
    ):
        mock_decode.return_value = {
            "type": "access",
            "jti": "token-id",
            "sub": "1",
            "iat": "bad-iat",
        }
        mock_blacklisted.return_value = False
        mock_get_user.return_value = MagicMock(id=1)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="token", db=db)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "令牌校验失败"


@pytest.mark.asyncio
async def test_refresh_access_token_rejects_invalid_iat_without_500():
    db = MagicMock()
    redis = MagicMock()
    redis.get = AsyncMock(return_value="200")

    with (
        patch("app.services.user_service.decode_token") as mock_decode,
        patch("app.services.user_service.is_token_blacklisted", new_callable=AsyncMock) as mock_blacklisted,
        patch("app.services.user_service.get_redis_client", return_value=redis),
        patch("app.services.user_service.user_crud.get_user_by_id") as mock_get_user,
    ):
        mock_decode.return_value = {
            "type": "refresh",
            "jti": "refresh-id",
            "sub": "1",
            "iat": "bad-iat",
        }
        mock_blacklisted.return_value = False
        mock_get_user.return_value = MagicMock(id=1)

        with pytest.raises(HTTPException) as exc_info:
            await UserService(db).refresh_access_token("refresh-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "令牌校验失败"
