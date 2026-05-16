import logging

import redis
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client: aioredis.Redis | None = None
_sync_redis_client: redis.Redis | None = None


async def init_redis_client() -> None:
    """初始化 Redis 异步客户端。"""
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    try:
        await redis_client.ping()
        logger.info("Redis 异步客户端初始化成功")
    except Exception:
        logger.exception("Redis 异步客户端初始化失败")
        raise


def init_sync_redis_client() -> None:
    """初始化 Redis 同步客户端。"""
    global _sync_redis_client
    _sync_redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
    try:
        _sync_redis_client.ping()
        logger.info("Redis 同步客户端初始化成功")
    except Exception:
        logger.exception("Redis 同步客户端初始化失败")
        raise


async def close_redis_client() -> None:
    """关闭 Redis 异步客户端。"""
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        logger.info("Redis 异步客户端关闭成功")
    redis_client = None


def close_sync_redis_client() -> None:
    """关闭 Redis 同步客户端。"""
    global _sync_redis_client
    if _sync_redis_client is not None:
        _sync_redis_client.close()
        logger.info("Redis 同步客户端关闭成功")
    _sync_redis_client = None


def get_redis_client() -> aioredis.Redis:
    """获取已初始化的 Redis 异步客户端。"""
    if redis_client is None:
        raise ValueError("Redis 客户端未初始化")
    return redis_client


def get_sync_redis_client() -> redis.Redis:
    """获取已初始化的 Redis 同步客户端。"""
    if _sync_redis_client is None:
        raise ValueError("Redis 同步客户端未初始化")
    return _sync_redis_client