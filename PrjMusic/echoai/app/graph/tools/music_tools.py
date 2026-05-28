"""
音乐操作工具。
读操作直接查 echomusic 数据库；写操作通过 SpringClient 调用 Spring API。
"""
from app.services.spring_client import AuthError, SpringApiError, spring_client
from app.utils.async_db import db_pools


class MusicToolError(Exception):
    """音乐工具异常。"""

    pass


async def search_music(keyword: str, limit: int = 10) -> list[dict]:
    """
    根据关键词搜索音乐（读操作，直接查 DB）。

    :param keyword: 搜索关键词（歌名或作者）
    :param limit: 返回数量上限
    :return: 音乐列表
    """
    pattern = f"%{keyword}%"
    async with db_pools.echomusic.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                id, music_name, author_ids, album_id, vip, hot,
                file_url, image1_url
            FROM musics
            WHERE is_deleted = FALSE
              AND music_name ILIKE $1
            ORDER BY hot DESC
            LIMIT $2
            """,
            pattern,
            limit,
        )

    return [
        {
            "id": row["id"],
            "name": row["music_name"],
            "author_ids": row["author_ids"] or [],
            "album_id": row["album_id"],
            "vip": row["vip"],
            "hot": row["hot"],
            "file_url": row["file_url"],
            "cover_url": row["image1_url"],
        }
        for row in rows
    ]


async def get_music_by_id(music_id: int) -> dict | None:
    """
    根据 ID 获取音乐详情（读操作，直接查 DB）。

    :param music_id: 音乐 ID
    :return: 音乐信息或 None
    """
    async with db_pools.echomusic.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                id, music_name, author_ids, album_id, vip, hot,
                file_url, image1_url
            FROM musics
            WHERE id = $1 AND is_deleted = FALSE
            """,
            music_id,
        )

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["music_name"],
        "author_ids": row["author_ids"] or [],
        "album_id": row["album_id"],
        "vip": row["vip"],
        "hot": row["hot"],
        "file_url": row["file_url"],
        "cover_url": row["image1_url"],
    }


async def get_user_playlists(user_id: int) -> list[dict]:
    """
    获取用户歌单列表（读操作，直接查 DB）。

    :param user_id: 用户 ID
    :return: 歌单列表
    """
    async with db_pools.echomusic.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, playlist_name, is_like, image_url
            FROM playlists
            WHERE user_id = $1
            ORDER BY is_like DESC, create_time DESC
            """,
            user_id,
        )

    return [
        {
            "id": row["id"],
            "name": row["playlist_name"],
            "is_like": row["is_like"],
            "cover_url": row["image_url"],
        }
        for row in rows
    ]


async def add_to_playlist(
    playlist_id: int, music_id: int, user_id: int, token: str
) -> dict:
    """
    将歌曲加入歌单（写操作，调用 Spring API）。

    :param playlist_id: 歌单 ID
    :param music_id: 音乐 ID
    :param user_id: 当前用户 ID（用于权限校验）
    :param token: JWT token
    :return: Spring API 响应
    :raises AuthError: JWT 过期
    :raises MusicToolError: 其他错误
    """
    # 权限校验：确认歌单属于当前用户
    async with db_pools.echomusic.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id FROM playlists WHERE id = $1",
            playlist_id,
        )
        if not row:
            raise MusicToolError("歌单不存在")
        if row["user_id"] != user_id:
            raise MusicToolError("无权操作他人歌单")

    # 调用 Spring API
    try:
        result = await spring_client.add_song_to_playlist(playlist_id, music_id, token)
    except AuthError:
        raise
    except SpringApiError as e:
        raise MusicToolError(f"加入歌单失败: {e}") from e

    return {"success": True, "playlist_id": playlist_id, "music_id": music_id}


async def play_music(music_id: int) -> dict | None:
    """
    获取播放所需的音乐结构化数据（读操作，直接查 DB）。

    :param music_id: 音乐 ID
    :return: 播放结构化数据或 None
    """
    music = await get_music_by_id(music_id)
    if not music:
        return None

    return {
        "action": "play",
        "music_id": music["id"],
        "music_name": music["name"],
        "author_ids": music["author_ids"],
        "cover_url": music["cover_url"],
        "file_url": music["file_url"],
        "vip": music["vip"],
    }
