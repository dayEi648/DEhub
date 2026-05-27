import logging
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def raise_not_found(resource_name: str) -> None:
    """抛出 404 异常（保持 detail 文本与各 Service 层历史一致）。"""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource_name}不存在")


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
    """HTTP 异常处理器（400/404 等主动抛出的业务异常）。"""
    if exc.status_code >= 500:
        extra = _build_log_extra(request, exc)
        logger.error("HTTP 异常: %s", exc.detail, extra=extra)

    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail},
    )


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 参数校验失败处理器（422）。"""
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
    """数据库异常处理器（500，隐藏堆栈）。"""
    extra = _build_log_extra(request, exc)
    logger.error("数据库异常: %s", exc, exc_info=(type(exc), exc, exc.__traceback__), extra=extra)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库异常，请稍后重试",
        },
    )


def catch_all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """全局兜底异常处理器（500）。"""
    extra = _build_log_extra(request, exc)
    logger.error("发生未捕获的异常: %s", exc, exc_info=(type(exc), exc, exc.__traceback__), extra=extra)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"code": 500, "message": "服务器内部错误"},
    )