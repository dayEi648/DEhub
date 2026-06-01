import logging
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1 import (
    agent_monitoring,
    users,
    blog_posts,
    blog_categories,
    comments,
    forum_zones,
    forum_posts,
    forum_replies,
    ai_chat as chat,
    user_favorites,
    uploads,
    system_logs,
    openapi_knowledge,
)
# 确保所有模型类被导入并注册到 Base.metadata
from app import models
from app.api.v1.openapi_knowledge import recover_pending_documents
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    catch_all_exception_handler,
)
from app.core.log_handler import SystemLogHandler
from app.redis_client import init_redis_client, close_redis_client, init_sync_redis_client, close_sync_redis_client, init_checkpoint_redis_client, close_checkpoint_redis_client
from app.infrastructure.llm_client import (
    init_llm_client, close_llm_client,
    init_llm_small_client, close_llm_small_client,
)
from app.infrastructure.embedding_client import init_embedding_client, close_embedding_client
from app.infrastructure.checkpoint_client import init_checkpoint_client, close_checkpoint_client
from app.infrastructure.background_tasks import background_task_manager
from app.core.config import settings
from contextlib import asynccontextmanager
from alembic.config import Config
from alembic import command


def _setup_system_log_handler() -> None:
    """将 SystemLogHandler 挂载到 root logger，避免重复挂载。"""
    root = logging.getLogger()
    if any(isinstance(h, SystemLogHandler) for h in root.handlers):
        return
    handler = SystemLogHandler()
    root.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    _setup_system_log_handler()

    # 数据库迁移：自动执行到最新版本（替代 Base.metadata.create_all）
    def _run_migrations() -> None:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    await asyncio.to_thread(_run_migrations)

    await init_redis_client()
    init_sync_redis_client()
    await init_checkpoint_redis_client()
    await init_llm_client()
    await init_llm_small_client()
    await init_embedding_client()
    await init_checkpoint_client()
    # 恢复因重启中断的 OpenAPI 解析任务
    recover_pending_documents()
    yield
    # 关闭时
    await background_task_manager.shutdown(timeout=10)
    await close_checkpoint_client()
    await close_embedding_client()
    close_llm_small_client()
    close_llm_client()
    close_sync_redis_client()
    await close_checkpoint_redis_client()
    await close_redis_client()

app = FastAPI(title="DE个人网站", version=settings.APP_VERSION, lifespan=lifespan)

# 注册全局异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, catch_all_exception_handler)

# 所有 v1 接口都以 /api/v1 为前缀
app.include_router(users.router, prefix="/api/v1")
app.include_router(blog_posts.router, prefix="/api/v1")
app.include_router(blog_categories.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(forum_zones.router, prefix="/api/v1")
app.include_router(forum_posts.router, prefix="/api/v1")
app.include_router(forum_replies.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(user_favorites.router_favorites, prefix="/api/v1")
app.include_router(user_favorites.router_follows, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(system_logs.router, prefix="/api/v1")
app.include_router(openapi_knowledge.router, prefix="/api/v1")
app.include_router(agent_monitoring.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Hello DEhub!"}
