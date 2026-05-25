"""LangGraph Checkpoint 客户端。

基于标准 Redis 的 AsyncRedisCheckpointSaver，无需 PostgreSQL。
"""

import logging

from app.core.config import settings
from app.redis_client import get_checkpoint_redis_client, get_sync_redis_client

from .redis_checkpoint import AsyncRedisCheckpointSaver

logger = logging.getLogger(__name__)

_CKPT_PREFIX = "dehub:ckpt"
_WRITE_PREFIX = "dehub:write"

_checkpointer: AsyncRedisCheckpointSaver | None = None


async def init_checkpoint_client() -> None:
    """初始化 Redis Checkpointer。

    在应用启动时调用一次，复用已有的 Redis 异步连接。
    """
    global _checkpointer

    redis = get_checkpoint_redis_client()
    _checkpointer = AsyncRedisCheckpointSaver(
        redis_client=redis,
        ttl_seconds=settings.REDIS_CHECKPOINT_TTL,
    )
    logger.info(
        "Checkpoint client initialized (Redis, TTL=%ds)",
        settings.REDIS_CHECKPOINT_TTL,
    )


def get_checkpointer() -> AsyncRedisCheckpointSaver:
    """获取已初始化的 Checkpointer 实例。"""
    if _checkpointer is None:
        raise ValueError("Checkpoint client 未初始化")
    return _checkpointer


async def close_checkpoint_client() -> None:
    """关闭 Checkpointer 引用。

    Redis 连接本身由 redis_client.py 统一管理生命周期。
    """
    global _checkpointer
    _checkpointer = None
    logger.info("Checkpoint client closed")


async def delete_checkpoint(thread_id: str) -> None:
    """删除指定 thread 的所有 checkpoint 数据。

    Args:
        thread_id: 对话线程 ID（对应 conversation_id）。
    """
    cp = get_checkpointer()
    await cp.adelete_thread(thread_id)
    logger.info("Deleted checkpoint for thread %s", thread_id)


def delete_checkpoint_sync(thread_id: str) -> None:
    """同步删除指定 thread 的 checkpoint 与 writes。

    用于同步上下文中（如 hard_delete_user）清理 Redis checkpoint 数据。
    """
    redis = get_sync_redis_client()
    pipe = redis.pipeline()
    for key in redis.scan_iter(match=f"{_CKPT_PREFIX}:{thread_id}:*"):
        pipe.delete(key)
    for key in redis.scan_iter(match=f"{_WRITE_PREFIX}:{thread_id}:*"):
        pipe.delete(key)
    pipe.execute()
    logger.info("Deleted checkpoint & writes for thread %s (sync)", thread_id)
