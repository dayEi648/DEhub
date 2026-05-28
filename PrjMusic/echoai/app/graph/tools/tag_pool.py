"""
合法标签池管理。
从 musics 表提取所有情绪/兴趣标签，缓存到 Redis（TTL 1小时）。
"""
import json

from app.utils.async_db import db_pools
from app.utils.redis_pool import redis_client


class TagPoolService:
    """标签池服务：管理情绪/兴趣标签的获取与缓存。"""

    REDIS_KEY = "ai:tags:pool"
    TTL = 3600  # 1小时

    async def get_tags(self) -> list[str]:
        """获取合法标签列表，优先读 Redis 缓存。"""
        cached = await redis_client.client.get(self.REDIS_KEY)
        if cached is not None:
            return json.loads(cached)

        # 从 PG 聚合所有标签
        async with db_pools.echomusic.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT UNNEST(emo_tags) AS tag
                FROM musics
                WHERE emo_tags IS NOT NULL
                  AND array_length(emo_tags, 1) > 0
                UNION
                SELECT DISTINCT UNNEST(interest_tags) AS tag
                FROM musics
                WHERE interest_tags IS NOT NULL
                  AND array_length(interest_tags, 1) > 0
                ORDER BY tag
                """
            )

        tags = [r["tag"] for r in rows if r["tag"]]
        await redis_client.client.setex(
            self.REDIS_KEY,
            self.TTL,
            json.dumps(tags, ensure_ascii=False),
        )
        return tags

    async def refresh(self) -> list[str]:
        """强制刷新标签缓存。"""
        await redis_client.client.delete(self.REDIS_KEY)
        return await self.get_tags()


# 全局单例
tag_pool_service = TagPoolService()
