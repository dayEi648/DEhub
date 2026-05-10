from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1 import users
from app.db.session import engine
from app.db.base import Base
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    catch_all_exception_handler,
)

app = FastAPI(title="DE个人网站", version="0.0.1")

# 注册全局异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, catch_all_exception_handler)

# 所有 v1 接口都以 /api/v1 为前缀
app.include_router(users.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Hello DEhub!"}