"""
健康检查路由。
"""
from fastapi import APIRouter

from app.utils.async_db import db_pools
from app.utils.redis_pool import redis_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    db_status = await db_pools.health_check()
    redis_status = await redis_client.health_check()

    all_ok = all(v == "connected" for v in db_status.values()) and redis_status == "connected"

    return {
        "code": 200,
        "msg": "ok" if all_ok else "some services unavailable",
        "data": {
            "status": "ok" if all_ok else "degraded",
            "db": db_status,
            "redis": redis_status,
        },
    }
