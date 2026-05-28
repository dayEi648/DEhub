"""
asyncpg 连接池封装，分别连接 echomusic 和 echovector。
"""
import asyncpg
from app.config import settings


class DatabasePools:
    """管理两个数据库连接池。"""

    def __init__(self):
        self.echomusic: asyncpg.Pool | None = None
        self.echovector: asyncpg.Pool | None = None

    async def connect(self):
        self.echomusic = await asyncpg.create_pool(
            dsn=settings.echomusic_db_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.db_command_timeout,
        )
        self.echovector = await asyncpg.create_pool(
            dsn=settings.echovector_db_url,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            command_timeout=settings.db_command_timeout,
        )

    async def disconnect(self):
        if self.echomusic:
            await self.echomusic.close()
            self.echomusic = None
        if self.echovector:
            await self.echovector.close()
            self.echovector = None

    async def health_check(self) -> dict:
        """检查两个数据库的连接状态。"""
        result = {}
        for name, pool in [("echomusic", self.echomusic), ("echovector", self.echovector)]:
            try:
                if pool is None:
                    result[name] = "not_initialized"
                    continue
                async with pool.acquire() as conn:
                    row = await conn.fetchrow("SELECT 1 AS ok")
                    result[name] = "connected" if row and row["ok"] == 1 else "failed"
            except Exception as e:
                result[name] = f"error: {type(e).__name__}"
        return result


# 全局单例
db_pools = DatabasePools()
