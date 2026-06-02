"""Redis 缓存基础设施。

提供安全的 JSON 序列化缓存读写、标签失效、TTL jitter 和 Redis 异常降级。
所有 Redis 操作均在 try/except 中捕获异常，失败时只记录 warning，不影响业务主流程。
"""

import hashlib
import json
import logging
import random
import secrets
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from app.core.config import settings
from app.redis_client import get_sync_redis_client

logger = logging.getLogger(__name__)

T = TypeVar("T")

CACHE_KEY_PREFIX = "dehub:cache:v1"
CACHE_TAG_PREFIX = "dehub:cachetag:v1"
CACHE_LOCK_PREFIX = "dehub:cachelock:v1"


def _get_redis():
    """获取 Redis 同步客户端；若未启用缓存或客户端异常则返回 None。"""
    if not settings.CACHE_ENABLED:
        return None
    try:
        return get_sync_redis_client()
    except Exception:
        logger.warning("Redis 客户端获取失败，缓存降级", exc_info=True)
        return None


def build_cache_key(namespace: str, params: dict | None = None) -> str:
    """构建缓存 key。

    Args:
        namespace: 命名空间，如 ``blog_posts:list``。
        params: 参数字典，会对 key 排序后取 sha256 前 16 位作为后缀，
            保证参数顺序不敏感。

    Returns:
        str: 完整 Redis key。
    """
    if params:
        # 过滤 None 值，减少 key 变化
        filtered = {k: v for k, v in sorted(params.items()) if v is not None}
        normalized = json.dumps(filtered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        param_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return f"{CACHE_KEY_PREFIX}:{namespace}:{param_hash}"
    return f"{CACHE_KEY_PREFIX}:{namespace}"


def get_json_cache(key: str, model_type: type[T]) -> T | None:
    """从缓存获取 JSON 数据并反序列化为指定类型。

    支持单个 ``BaseModel`` 子类或泛型容器（如 ``list[ForumZoneResponse]``）。
    反序列化失败时会自动删除该 key 并返回 ``None``，避免脏数据长期滞留。

    Args:
        key: Redis key。
        model_type: 目标类型。

    Returns:
        T | None: 反序列化后的对象，未命中或失败时返回 None。
    """
    redis = _get_redis()
    if redis is None:
        return None
    try:
        raw = redis.get(key)
        if raw is None:
            return None
        if isinstance(model_type, type) and issubclass(model_type, BaseModel):
            return model_type.model_validate_json(raw)
        return TypeAdapter(model_type).validate_json(raw)
    except Exception:
        logger.warning("缓存反序列化失败，key=%s", key, exc_info=True)
        try:
            redis.delete(key)
        except Exception:
            pass
        return None


def set_json_cache(
    key: str,
    value: BaseModel | list[BaseModel],
    ttl: int,
    tags: list[str] | None = None,
) -> None:
    """将 Pydantic 模型序列化为 JSON 存入缓存。

    写入时会为 TTL 增加 ±10% 的随机抖动，防止大量 key 同时过期引发缓存雪崩。
    同时会将 key 登记到对应的 tag set 中，便于按标签批量失效。

    Args:
        key: Redis key。
        value: 待缓存的值，支持单个 BaseModel 或 BaseModel 列表。
        ttl: 过期时间（秒）。
        tags: 标签列表，用于批量失效。
    """
    redis = _get_redis()
    if redis is None:
        return
    try:
        jittered_ttl = max(1, int(ttl * (1 + random.uniform(-0.1, 0.1))))
        if isinstance(value, BaseModel):
            json_data = value.model_dump_json()
        elif isinstance(value, list):
            json_data = json.dumps([item.model_dump(mode="json") for item in value])
        else:
            raise TypeError(f"不支持的缓存值类型: {type(value)}")
        redis.setex(key, jittered_ttl, json_data)

        if tags:
            for tag in tags:
                tag_key = f"{CACHE_TAG_PREFIX}:{tag}"
                redis.sadd(tag_key, key)
                # tag set 的 TTL 略长于业务 key，避免 key 未过期但 tag 已丢失
                redis.expire(tag_key, jittered_ttl + 60)
    except Exception:
        logger.warning("缓存写入失败，key=%s", key, exc_info=True)


def invalidate_cache_tags(tags: list[str]) -> None:
    """按标签批量失效缓存。

    通过 ``SMEMBERS`` 获取每个 tag 下登记的所有 key，然后使用 pipeline
    批量 ``DELETE`` 这些 key 和 tag set 本身。

    Args:
        tags: 待失效的标签列表。
    """
    redis = _get_redis()
    if redis is None:
        return
    try:
        pipe = redis.pipeline()
        for tag in tags:
            tag_key = f"{CACHE_TAG_PREFIX}:{tag}"
            keys = redis.smembers(tag_key)
            if keys:
                pipe.delete(*keys, tag_key)
        pipe.execute()
    except Exception:
        logger.warning("缓存失效失败，tags=%s", tags, exc_info=True)


def acquire_cache_lock(key: str, ttl: int = 5) -> str | None:
    """获取缓存重建锁（用于热点 key 防击穿）。

    Args:
        key: 业务 key，锁 key 会在此基础上增加前缀。
        ttl: 锁的过期时间（秒），默认 5 秒。

    Returns:
        str | None: 成功时返回锁 token，失败时返回 None。
    """
    redis = _get_redis()
    if redis is None:
        return None
    try:
        lock_key = f"{CACHE_LOCK_PREFIX}:{key}"
        token = secrets.token_urlsafe(8)
        acquired = redis.set(lock_key, token, nx=True, ex=ttl) is True
        return token if acquired else None
    except Exception:
        return None


def release_cache_lock(key: str, token: str | None = None) -> None:
    """释放缓存重建锁。

    仅在 token 与 Redis 中存储的值一致时才删除，避免误删他人持有的锁。

    Args:
        key: 业务 key。
        token: 获取锁时返回的 token。为 None 时不执行删除。
    """
    redis = _get_redis()
    if redis is None or token is None:
        return
    try:
        lock_key = f"{CACHE_LOCK_PREFIX}:{key}"
        current = redis.get(lock_key)
        if current and current.decode("utf-8") == token:
            redis.delete(lock_key)
    except Exception:
        pass
