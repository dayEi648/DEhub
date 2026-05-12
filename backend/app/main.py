from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1 import users, blog_posts, blog_categories, comments, forum_zones, forum_posts, forum_replies
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    catch_all_exception_handler,
)
from app.redis_client import init_redis_client, close_redis_client
from contextlib import asynccontextmanager






@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await init_redis_client()
    yield
    # 关闭时
    await close_redis_client()

app = FastAPI(title="DE个人网站", version="0.0.1", lifespan=lifespan)

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

@app.get("/")
def root():
    return {"message": "Hello DEhub!"}