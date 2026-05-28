"""
全局异常处理器。
统一将异常包装为 {code, msg, data} 格式，与 Spring Result 保持一致。
"""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """处理 FastAPI HTTPException。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": exc.detail,
            "data": None,
        },
    )


async def global_exception_handler(request: Request, exc: Exception):
    """处理未捕获的通用异常。"""
    # 记录异常详情，便于排查
    logger.exception("未捕获的异常: %s %s", request.method, request.url.path)
    # 生产环境不应暴露详细错误信息给客户端
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "服务器内部错误",
            "data": None,
        },
    )
