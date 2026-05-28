"""
Redis 异步客户端封装。
"""
from redis.asyncio import Redis
from app.config import settings


class RedisClient:
    """管理 Redis 异步连接。"""

    def __init__(self):
        self.client: Redis | None = None

    async def connect(self):
        self.client = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    async def disconnect(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def health_check(self) -> str:
        """检查 Redis 连接状态。"""
        try:
            if self.client is None:
                return "not_initialized"
            pong = await self.client.ping()
            return "connected" if pong else "failed"
        except Exception as e:
            return f"error: {type(e).__name__}"


# 全局单例
redis_client = RedisClient()
