import asyncio
import logging
from collections.abc import Iterator

from sqlalchemy import case, update

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.blog_post import BlogPost
from app.models.forum_post import ForumPost
from app.redis_client import get_sync_redis_client

logger = logging.getLogger(__name__)

BLOG_VIEW_COUNT_PREFIX = "dehub:view_count:blog"
FORUM_POST_VIEW_COUNT_PREFIX = "dehub:view_count:forum_post"


def _get_redis():
    """获取 Redis 同步客户端；若未启用缓存或客户端异常则返回 None。"""
    if not settings.CACHE_ENABLED:
        return None
    try:
        return get_sync_redis_client()
    except Exception:
        logger.warning("Redis 客户端获取失败，浏览量计数降级", exc_info=True)
        return None


def _batch_dict(d: dict, batch_size: int) -> Iterator[dict]:
    """将字典按批次切分。"""
    items = list(d.items())
    for i in range(0, len(items), batch_size):
        yield dict(items[i : i + batch_size])


class ViewCounter:
    """浏览量计数器。

    使用 Redis 作为写缓冲区，消除详情页访问对数据库的直接写操作。
    后台协程定期将增量批量回写到数据库。
    """

    # ---------- 写入（用户访问详情页时调用）----------

    @staticmethod
    def incr_blog_view_count(post_id: int, db=None) -> None:
        """增加博客浏览量计数器。

        优先写入 Redis Counter；若 Redis 不可用且提供了数据库 session，
        则降级为直接 UPDATE 数据库（保持与旧行为兼容，便于测试环境）。
        """
        redis = _get_redis()
        if redis is not None:
            try:
                redis.incr(f"{BLOG_VIEW_COUNT_PREFIX}:{post_id}")
                return
            except Exception:
                logger.warning("博客浏览量 Redis 计数失败: post_id=%s", post_id, exc_info=True)
        if db is not None:
            try:
                from app.crud import blog_post as blog_post_crud
                blog_post_crud.increment_view_count(db, post_id)
            except Exception:
                logger.warning("博客浏览量数据库降级写入失败: post_id=%s", post_id, exc_info=True)

    @staticmethod
    def incr_forum_post_view_count(post_id: int, db=None) -> None:
        """增加论坛帖子浏览量计数器。

        优先写入 Redis Counter；若 Redis 不可用且提供了数据库 session，
        则降级为直接 UPDATE 数据库。
        """
        redis = _get_redis()
        if redis is not None:
            try:
                redis.incr(f"{FORUM_POST_VIEW_COUNT_PREFIX}:{post_id}")
                return
            except Exception:
                logger.warning("论坛帖子浏览量 Redis 计数失败: post_id=%s", post_id, exc_info=True)
        if db is not None:
            try:
                from app.crud import forum_post as forum_post_crud
                forum_post_crud.increment_post_view_count(db, post_id)
            except Exception:
                logger.warning("论坛帖子浏览量数据库降级写入失败: post_id=%s", post_id, exc_info=True)

    # ---------- 读取（返回合并后的浏览量）----------

    @staticmethod
    def get_blog_view_count(post_id: int, db_value: int) -> int:
        """获取合并后的博客浏览量（DB值 + Redis增量）。"""
        redis = _get_redis()
        if redis is None:
            return db_value
        try:
            delta = int(redis.get(f"{BLOG_VIEW_COUNT_PREFIX}:{post_id}") or 0)
            return db_value + delta
        except Exception:
            return db_value

    @staticmethod
    def get_forum_post_view_count(post_id: int, db_value: int) -> int:
        """获取合并后的论坛帖子浏览量（DB值 + Redis增量）。"""
        redis = _get_redis()
        if redis is None:
            return db_value
        try:
            delta = int(redis.get(f"{FORUM_POST_VIEW_COUNT_PREFIX}:{post_id}") or 0)
            return db_value + delta
        except Exception:
            return db_value

    # ---------- 回写（后台协程调用）----------

    @staticmethod
    def flush_to_db() -> None:
        """将 Redis 中的浏览量增量批量回写到数据库。

        使用 SCAN 遍历所有计数器 key，批量读取后一次性 UPDATE，
        最后删除已回写的 key。
        """
        redis = _get_redis()
        if redis is None:
            return

        blog_keys = ViewCounter._scan_keys(f"{BLOG_VIEW_COUNT_PREFIX}:*")
        forum_keys = ViewCounter._scan_keys(f"{FORUM_POST_VIEW_COUNT_PREFIX}:*")

        if not blog_keys and not forum_keys:
            return

        all_keys = blog_keys + forum_keys
        pipe = redis.pipeline()
        for key in all_keys:
            pipe.get(key)
        values = pipe.execute()

        blog_deltas: dict[int, int] = {}
        for key, val in zip(blog_keys, values[: len(blog_keys)]):
            if val:
                post_id = int(key.decode().split(":")[-1])
                blog_deltas[post_id] = int(val)

        forum_deltas: dict[int, int] = {}
        for key, val in zip(forum_keys, values[len(blog_keys) :]):
            if val:
                post_id = int(key.decode().split(":")[-1])
                forum_deltas[post_id] = int(val)

        db = SessionLocal()
        try:
            if blog_deltas:
                for batch in _batch_dict(blog_deltas, 100):
                    case_stmt = case(
                        *[(BlogPost.id == pid, delta) for pid, delta in batch.items()],
                        else_=0,
                    )
                    db.execute(
                        update(BlogPost)
                        .where(BlogPost.id.in_(batch.keys()))
                        .values(view_count=BlogPost.view_count + case_stmt)
                    )

            if forum_deltas:
                for batch in _batch_dict(forum_deltas, 100):
                    case_stmt = case(
                        *[(ForumPost.id == pid, delta) for pid, delta in batch.items()],
                        else_=0,
                    )
                    db.execute(
                        update(ForumPost)
                        .where(ForumPost.id.in_(batch.keys()))
                        .values(view_count=ForumPost.view_count + case_stmt)
                    )

            db.commit()
            logger.info(
                "浏览量回写完成: blog=%s, forum=%s",
                len(blog_deltas),
                len(forum_deltas),
            )

            pipe = redis.pipeline()
            for key in all_keys:
                pipe.delete(key)
            pipe.execute()

        except Exception:
            db.rollback()
            logger.exception("浏览量回写失败")
        finally:
            db.close()

    @staticmethod
    def _scan_keys(pattern: str) -> list:
        """使用 SCAN 安全遍历 Redis key，避免 KEYS 命令阻塞。"""
        redis = _get_redis()
        if redis is None:
            return []
        keys = []
        cursor = 0
        while True:
            cursor, batch = redis.scan(cursor=cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
        return keys


async def view_counter_flush_loop() -> None:
    """浏览量回写后台协程。

    在应用启动时由 lifespan 注册，持续运行直到应用关闭。
    """
    while True:
        try:
            await asyncio.to_thread(ViewCounter.flush_to_db)
        except Exception:
            logger.exception("浏览量回写循环异常")
        await asyncio.sleep(settings.VIEW_COUNTER_FLUSH_INTERVAL_SECONDS)
