"""
个性推荐节点。
基于情绪/兴趣标签查询 musics 表，排除已推荐过的音乐，按热度排序。
"""
from app.graph.state import AgentState
from app.utils.async_db import db_pools


RECOMMEND_LIMIT = 5


async def recommend_node(state: AgentState) -> dict:
    """
    个性推荐节点。
    根据意图（emotion_recommend / interest_recommend）查询对应标签的音乐，
    排除当前会话已推荐过的，按热度排序。
    无结果时降级为全局热歌推荐。
    """
    user_id = state["user_id"]
    session_id = state["session_id"]
    intent = state.get("intent", "")

    if intent == "emotion_recommend":
        tags = state.get("emotion_tags", [])
        tag_column = "emo_tags"
        recommend_type = "emotion"
    elif intent == "interest_recommend":
        tags = state.get("interest_tags", [])
        tag_column = "interest_tags"
        recommend_type = "interest"
    elif intent == "profile_recommend":
        # 从用户画像读取标签，走独立查询逻辑
        recommend_type = "profile"
        user_tags = await _get_user_tags(user_id)
        tags = user_tags["emotion"] + user_tags["interest"]
        if not tags:
            return {
                "tool_results": [
                    {
                        "tool": "profile_recommend",
                        "status": "no_tags",
                        "message": "暂无个人标签，请先完善听歌偏好",
                    }
                ]
            }
        results = await _query_by_user_tags(
            user_id=user_id,
            session_id=session_id,
            emotion_tags=user_tags["emotion"],
            interest_tags=user_tags["interest"],
            limit=RECOMMEND_LIMIT,
        )
        # 跳过下方统一的 _query_by_tags 调用
        tag_column = None
    else:
        return {"tool_results": []}

    if intent != "profile_recommend" and not tags:
        return {
            "tool_results": [
                {
                    "tool": recommend_type + "_recommend",
                    "status": "no_tags",
                    "message": "未识别到有效标签，无法推荐",
                }
            ]
        }

    # 查询匹配标签且未推荐过的音乐（profile_recommend 已在上方查询）
    if intent != "profile_recommend":
        results = await _query_by_tags(
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            tag_column=tag_column,
            limit=RECOMMEND_LIMIT,
        )

    # 降级：无结果时推荐全局热歌
    fallback = False
    if not results:
        results = await _query_hot_fallback(
            user_id=user_id,
            session_id=session_id,
            limit=RECOMMEND_LIMIT,
        )
        fallback = True

    if not results:
        return {
            "tool_results": [
                {
                    "tool": recommend_type + "_recommend",
                    "status": "empty",
                    "message": "未找到匹配的音乐",
                }
            ]
        }

    # 写入推荐日志
    music_ids = [m["id"] for m in results]
    await _save_recommend_log(session_id, user_id, recommend_type, tags, music_ids)

    return {
        "tool_results": [
            {
                "tool": recommend_type + "_recommend",
                "status": "fallback_hot" if fallback else "ok",
                "tags": tags,
                "fallback": fallback,
                "recommendations": results,
            }
        ]
    }


# 合法标签列白名单，禁止动态拼接任意列名
_TAG_COLUMN_MAP = {
    "emo_tags": "emo_tags",
    "interest_tags": "interest_tags",
}


async def _get_user_tags(user_id: int) -> dict:
    """读取用户的 emo_tags 和 interest_tags。"""
    async with db_pools.echomusic.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT emo_tags, interest_tags FROM users WHERE id = $1",
            user_id,
        )
    if not row:
        return {"emotion": [], "interest": []}
    return {
        "emotion": row["emo_tags"] or [],
        "interest": row["interest_tags"] or [],
    }


async def _query_by_user_tags(
    user_id: int,
    session_id: str,
    emotion_tags: list[str],
    interest_tags: list[str],
    limit: int,
) -> list[dict]:
    """
    基于用户画像标签查询音乐。
    同时匹配 emo_tags 和 interest_tags（并集），排除已推荐过的。
    """
    async with db_pools.echomusic.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT ON (m.id)
                m.id, m.music_name, m.author_ids, m.image1_url, m.file_url, m.vip, m.hot
            FROM musics m
            WHERE m.is_deleted = FALSE
              AND (
                  m.emo_tags && $1::text[]
                  OR m.interest_tags && $2::text[]
              )
              AND NOT EXISTS (
                  SELECT 1 FROM ai_recommend_logs r
                  WHERE r.session_id = $3 AND r.user_id = $4
                    AND m.id = ANY(r.music_ids)
              )
            ORDER BY m.id, m.hot DESC
            LIMIT $5
            """,
            emotion_tags,
            interest_tags,
            session_id,
            user_id,
            limit,
        )

    return [
        {
            "id": row["id"],
            "name": row["music_name"],
            "author_ids": row["author_ids"] or [],
            "cover_url": row["image1_url"],
            "file_url": row["file_url"],
            "vip": row["vip"],
            "hot": row["hot"],
        }
        for row in rows
    ]


async def _query_by_tags(
    user_id: int,
    session_id: str,
    tags: list[str],
    tag_column: str,
    limit: int,
) -> list[dict]:
    """
    查询包含指定标签且未被当前会话推荐过的音乐。
    任一标签匹配即可（使用 && 操作符检查数组交集）。
    """
    if tag_column not in _TAG_COLUMN_MAP:
        raise ValueError(f"非法标签列: {tag_column}")
    safe_column = _TAG_COLUMN_MAP[tag_column]
    tag_array = tags

    async with db_pools.echomusic.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT
                m.id, m.music_name, m.author_ids, m.image1_url, m.file_url, m.vip, m.hot
            FROM musics m
            WHERE m.is_deleted = FALSE
              AND m.{safe_column} && $1::text[]
              AND NOT EXISTS (
                  SELECT 1 FROM ai_recommend_logs r
                  WHERE r.session_id = $2 AND r.user_id = $3
                    AND m.id = ANY(r.music_ids)
              )
            ORDER BY m.hot DESC
            LIMIT $4
            """,
            tag_array,
            session_id,
            user_id,
            limit,
        )

    return [
        {
            "id": row["id"],
            "name": row["music_name"],
            "author_ids": row["author_ids"] or [],
            "cover_url": row["image1_url"],
            "file_url": row["file_url"],
            "vip": row["vip"],
            "hot": row["hot"],
        }
        for row in rows
    ]


async def _query_hot_fallback(
    user_id: int,
    session_id: str,
    limit: int,
) -> list[dict]:
    """全局热歌降级推荐。"""
    async with db_pools.echomusic.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                m.id, m.music_name, m.author_ids, m.image1_url, m.file_url, m.vip, m.hot
            FROM musics m
            WHERE m.is_deleted = FALSE
              AND NOT EXISTS (
                  SELECT 1 FROM ai_recommend_logs r
                  WHERE r.session_id = $1 AND r.user_id = $2
                    AND m.id = ANY(r.music_ids)
              )
            ORDER BY m.hot DESC
            LIMIT $3
            """,
            session_id,
            user_id,
            limit,
        )

    return [
        {
            "id": row["id"],
            "name": row["music_name"],
            "author_ids": row["author_ids"] or [],
            "cover_url": row["image1_url"],
            "file_url": row["file_url"],
            "vip": row["vip"],
            "hot": row["hot"],
        }
        for row in rows
    ]


async def _save_recommend_log(
    session_id: str,
    user_id: int,
    recommend_type: str,
    tags: list[str],
    music_ids: list[int],
) -> None:
    """写入推荐日志。"""
    async with db_pools.echomusic.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO ai_recommend_logs (session_id, user_id, recommend_type, target_tags, music_ids)
            VALUES ($1, $2, $3, $4, $5)
            """,
            session_id,
            user_id,
            recommend_type,
            tags,
            music_ids,
        )
