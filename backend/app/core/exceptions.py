import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def _build_log_extra(request: Request, exc: Exception) -> dict:
    """构造日志 extra 字段，供 SystemLogHandler 提取结构化上下文。"""
    extra: dict = {
        "extra": {
            "error_type": exc.__class__.__name__,
            "error_detail": str(exc),
        }
    }

    if request.client:
        extra["ip"] = request.client.host

    trace_id = request.headers.get("x-request-id")
    if trace_id:
        extra["trace_id"] = trace_id

    return extra


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTP 异常处理器
    处理主动抛出的 HTTPException（如 400 用户名已存在、404 用户不存在）
    Args:
        request: 请求对象
        exc: HTTP 异常对象
    Returns:
        JSONResponse: JSON 响应
    """
    if exc.status_code >= 500:
        extra = _build_log_extra(request, exc)
        logger.error("HTTP 异常: %s", exc.detail, extra=extra)

    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail},
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Validation 异常处理器
    处理 Pydantic 参数校验失败（如 email 格式不对、必填字段缺失）
    Args:
        request: 请求对象
        exc: Validation 异常对象
    Returns:
        JSONResponse: JSON 响应
    """
    extra = _build_log_extra(request, exc)
    extra["extra"]["validation_errors"] = exc.errors()
    logger.warning("请求参数校验失败: %s", exc.errors(), extra=extra)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求参数校验失败",
            "detail": exc.errors()
        },
    )


def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    SQLAlchemy 异常处理器
    处理数据库异常（如连接断开、约束冲突）
    Args:
        request: 请求对象
        exc: SQLAlchemy 异常对象
    Returns:
        JSONResponse: JSON 响应
    """
    extra = _build_log_extra(request, exc)
    logger.error("数据库异常: %s", exc, exc_info=True, extra=extra)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库异常，请稍后重试",
        },
    )


def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    全局异常处理器
    兜底：捕获所有未预料的异常，防止泄露堆栈信息
    Args:
        request: 请求对象
        exc: 异常对象
    Returns:
        JSONResponse: JSON 响应
    """
    extra = _build_log_extra(request, exc)
    logger.error("发生未捕获的异常: %s", exc, exc_info=True, extra=extra)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务器内部错误"},
    )