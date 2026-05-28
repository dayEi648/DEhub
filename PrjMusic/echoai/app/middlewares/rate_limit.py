"""
单用户限流中间件。
基于 Redis 实现滑动窗口计数，限制单用户 10 请求/分钟。
"""
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.utils.redis_pool import redis_client

RATE_LIMIT = 10          # 每窗口最多请求数
WINDOW_SECONDS = 60      # 窗口时长（秒）
RATE_LIMIT_PREFIX = "ai:rate_limit"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件。
    对携带有效 JWT 的请求按 user_id 计数；未携带 JWT 的请求按 IP 计数。
    """

    async def dispatch(self, request: Request, call_next):
        # 跳过健康检查（避免影响监控）
        if request.url.path == "/health" or request.url.path == "/":
            return await call_next(request)

        # 跳过只读请求（避免影响用户频繁切换会话查看历史消息）
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        identifier = await self._get_identifier(request)
        key = f"{RATE_LIMIT_PREFIX}:{identifier}"

        # 检查并增加计数
        current = await self._increment_and_check(key)
        if current > RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "msg": "请求过于频繁，请稍后再试",
                    "data": None,
                },
            )

        # 在响应头中附加剩余配额（可选）
        remaining = max(0, RATE_LIMIT - current)
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
        return response

    async def _get_identifier(self, request: Request) -> str:
        """获取请求标识：有 JWT 用 user_id，否则用 IP。"""
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_exp": False},  # 限流不验证过期，留给鉴权依赖处理
                )
                user_id = payload.get("userId")
                if user_id is not None:
                    return f"user:{user_id}"
            except Exception:
                pass

        # fallback 到客户端直接连接 IP（不使用 X-Forwarded-For，防止客户端伪造 IP 绕过限流）
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    async def _increment_and_check(self, key: str) -> int:
        """
        使用 Redis 原子操作实现固定窗口计数。
        首次设置时使用 SET NX EX 原子初始化，避免 INCR+EXPIRE 竞态导致 key 永不过期。
        """
        if redis_client.client is None:
            # Redis 未连接时不限流（降级）
            return 0

        # 原子初始化：仅当 key 不存在时设置值为 1 并附加过期时间
        init_ok = await redis_client.client.set(key, "1", nx=True, ex=WINDOW_SECONDS)
        if init_ok:
            return 1

        # key 已存在，直接自增
        return await redis_client.client.incr(key)
