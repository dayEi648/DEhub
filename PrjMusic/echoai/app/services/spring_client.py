"""
Spring Boot 后端 HTTP 客户端。
AI 服务通过本客户端携带原 JWT 调用 Spring API 完成写操作。
"""
import httpx
from urllib.parse import quote

from app.config import settings


class AuthError(Exception):
    """JWT 鉴权过期或无效。"""

    pass


class SpringApiError(Exception):
    """Spring API 调用异常。"""

    pass


class SpringClient:
    """Spring Boot API 异步客户端。"""

    def __init__(self):
        self._base = settings.spring_base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=15.0)

    def _headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def close(self):
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        token: str,
        **kwargs,
    ) -> dict:
        """
        发送 HTTP 请求并处理响应。

        :raises AuthError: 401/403 响应（JWT 过期）
        :raises SpringApiError: 其他错误响应
        """
        url = f"{self._base}{path}"
        headers = self._headers(token)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        response = await self._client.request(
            method, url, headers=headers, **kwargs
        )

        if response.status_code == 401:
            raise AuthError("登录已过期，请重新登录后重试")
        if response.status_code == 403:
            raise AuthError("权限不足，无法执行该操作")
        if response.status_code >= 400:
            raise SpringApiError(
                f"Spring API 错误 ({response.status_code}): {response.text[:200]}"
            )

        try:
            return response.json()
        except Exception:
            return {"raw": response.text}

    # ========== 音乐/歌单操作 ==========

    async def search_music(self, keyword: str, token: str) -> dict:
        """搜索音乐。"""
        return await self._request(
            "GET",
            f"/api/musics/search?keyword={quote(keyword)}",
            token=token,
        )

    async def add_song_to_playlist(
        self, playlist_id: int, music_id: int, token: str
    ) -> dict:
        """将歌曲加入歌单。"""
        return await self._request(
            "POST",
            f"/api/playlists/{playlist_id}/songs/{music_id}",
            token=token,
        )


# 全局单例
spring_client = SpringClient()
