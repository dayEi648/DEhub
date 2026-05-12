from sqlalchemy.orm import Session
from app.crud import forum_zone as forum_zone_crud
from app.redis_client import get_sync_redis_client


def _get_zone_manager_cache_key(zone_id: int) -> str:
    """获取分区区主缓存的 Redis Key"""
    return f"forum_zone:manager:{zone_id}"


def get_zone_manager_id(db: Session, zone_id: int) -> int | None:
    """
    获取分区区主 ID，优先读 Redis 缓存
    Args:
        db: 数据库会话
        zone_id: 分区ID
    Returns:
        int | None: 区主用户ID，分区不存在时返回 None
    """
    redis = get_sync_redis_client()
    cache_key = _get_zone_manager_cache_key(zone_id)
    cached = redis.get(cache_key)
    if cached is not None:
        return int(cached)

    zone = forum_zone_crud.get_zone_by_id(db, zone_id)
    if zone is None:
        return None
    redis.set(cache_key, zone.manager_id)
    return zone.manager_id


def set_zone_manager_cache(zone_id: int, manager_id: int) -> None:
    """更新分区区主缓存"""
    redis = get_sync_redis_client()
    redis.set(_get_zone_manager_cache_key(zone_id), manager_id)


def delete_zone_manager_cache(zone_id: int) -> None:
    """删除分区区主缓存"""
    redis = get_sync_redis_client()
    redis.delete(_get_zone_manager_cache_key(zone_id))


def is_zone_manager(db: Session, zone_id: int, user_id: int) -> bool:
    """
    判断指定用户是否为某分区的区主
    Args:
        db: 数据库会话
        zone_id: 分区ID
        user_id: 用户ID
    Returns:
        bool: 是否为区主
    """
    manager_id = get_zone_manager_id(db, zone_id)
    if manager_id is None:
        return False
    return manager_id == user_id
