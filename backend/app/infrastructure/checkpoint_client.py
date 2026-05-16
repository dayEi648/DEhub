"""LangGraph Checkpoint 客户端。

管理 PostgreSQL 连接池与 AsyncPostgresSaver 生命周期。
"""

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


async def init_checkpoint_client() -> None:
    """初始化 Checkpoint 连接池与数据库表结构。

    在应用启动时调用一次，创建连接池并执行 setup() 建表。
    """
    global _pool, _checkpointer

    conninfo = settings.DATABASE_URL
    _pool = AsyncConnectionPool(
        conninfo=conninfo,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        },
        open=False,
    )
    await _pool.open()

    _checkpointer = AsyncPostgresSaver(conn=_pool)
    await _checkpointer.setup()
    logger.info("Checkpoint client initialized")


def get_checkpointer() -> AsyncPostgresSaver:
    """获取已初始化的 AsyncPostgresSaver 实例。"""
    if _checkpointer is None:
        raise ValueError("Checkpoint client 未初始化")
    return _checkpointer


async def close_checkpoint_client() -> None:
    """关闭 Checkpoint 连接池。

    在应用关闭时调用。
    """
    global _pool, _checkpointer
    _checkpointer = None
    if _pool is not None:
        await _pool.close()
        _pool = None
    logger.info("Checkpoint client closed")


async def delete_checkpoint(thread_id: str) -> None:
    """删除指定 thread 的所有 checkpoint 数据。

    Args:
        thread_id: 对话线程 ID（对应 conversation_id）。
    """
    cp = get_checkpointer()
    await cp.adelete_thread(thread_id)
    logger.info("Deleted checkpoint for thread %s", thread_id)
