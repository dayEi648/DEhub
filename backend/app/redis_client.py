import redis.asyncio as aioredis
from redis import Redis
from app.core.config import settings

redis_client: aioredis.Redis | None = None
_sync_redis_client: Redis | None = None

def get_sync_redis_client() -> Redis:
    """
    获取同步 Redis 客户端（懒加载）
    """
    global _sync_redis_client
    if _sync_redis_client is None:
        _sync_redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    return _sync_redis_client

async def init_redis_client() -> None:
    """
    初始化Redis客户端
    """
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
    )
    try:
        await redis_client.ping()
        print("Redis客户端初始化成功")
    except Exception as e:
        print(f"Redis客户端初始化失败: {e}")
        raise e

async def close_redis_client() -> None:
    """
    关闭Redis客户端
    """
    global redis_client
    if redis_client:
        await redis_client.close()
    print("Redis客户端关闭成功")

def get_redis_client() -> aioredis.Redis:
    """
    获取Redis客户端
    """
    if not redis_client:
        raise ValueError("Redis客户端未初始化")
    return redis_client