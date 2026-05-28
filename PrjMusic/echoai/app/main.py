"""
FastAPI 应用入口。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.utils.async_db import db_pools
from app.utils.redis_pool import redis_client
from app.graph.tools.tag_pool import tag_pool_service
from app.routers import health, chat, knowledge, sessions
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.exception_handler import (
    http_exception_handler,
    global_exception_handler,
)
from app.services.spring_client import spring_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动
    await db_pools.connect()
    await redis_client.connect()
    # 预热标签池（首次启动时加载到 Redis）
    await tag_pool_service.get_tags()
    yield
    # 关闭
    await spring_client.close()
    await db_pools.disconnect()
    await redis_client.disconnect()


app = FastAPI(
    title="EchoAI Agent Service",
    description="基于 LangGraph 的 Python AI 服务",
    version="0.1.0",
    lifespan=lifespan,
)

# 全局异常处理器（确保统一响应格式）
# StarletteHTTPException 覆盖 404 路由未找到等场景
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
# 其他未捕获异常兜底
app.add_exception_handler(Exception, global_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 单用户限流中间件（10 req/min）
app.add_middleware(RateLimitMiddleware)

# 注册路由
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(knowledge.router)


@app.get("/")
async def root():
    return {"code": 200, "msg": "EchoAI Agent Service is running", "data": None}


@app.get("/debug/routes")
async def debug_routes():
    """调试端点：查看注册的路由。"""
    routes = []
    for r in app.routes:
        if hasattr(r, "path"):
            routes.append(r.path)
    return {"code": 200, "msg": "ok", "data": {"routes": routes}}
