import logging
import threading
import traceback
from typing import Any

from app.db.session import SessionLocal
from app.models.system_log import SystemLog

_thread_local = threading.local()


class SystemLogHandler(logging.Handler):
    """
    自定义日志处理器，将 WARN 及以上级别日志持久化到 PostgreSQL。

    通过 ``logging.Logger`` 的 ``extra`` 参数可传递结构化上下文：

    .. code-block:: python

        logger.warning(
            "支付回调验签失败",
            extra={
                "trace_id": "abc-123",
                "user_id": 42,
                "extra": {"order_id": "ORD-001", "amount": 199.9},
            },
        )

    支持的 extra 字段：
    - ``trace_id``   : 请求链路追踪 ID
    - ``user_id``    : 当前操作用户 ID
    - ``ip``         : 客户端 IP（字符串）
    - ``extra``      : 任意字典，写入 JSONB 字段
    """

    def __init__(self) -> None:
        super().__init__()
        self.setLevel(logging.WARNING)

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.WARNING:
            return

        # 防递归：若当前线程正在写入日志，则直接返回，
        # 避免"数据库写入失败→记录错误日志→再次触发 Handler"的死循环。
        if getattr(_thread_local, "emitting", False):
            return
        _thread_local.emitting = True

        try:
            self._persist(record)
        except Exception:
            # 日志写入失败不应影响主业务流程，静默丢弃。
            pass
        finally:
            _thread_local.emitting = False

    def _persist(self, record: logging.LogRecord) -> None:
        message = record.getMessage()

        exception_text: str | None = None
        if record.exc_info:
            exception_text = "".join(
                traceback.format_exception(*record.exc_info)
            )

        # 从 extra 提取自定义字段；缺失则使用 None
        trace_id: str | None = getattr(record, "trace_id", None)
        user_id: int | None = getattr(record, "user_id", None)
        ip: str | None = getattr(record, "ip", None)
        extra_data: dict[str, Any] | None = getattr(record, "extra", None)

        log_entry = SystemLog(
            level=record.levelname,
            module=record.name,
            message=message,
            exception=exception_text,
            trace_id=trace_id,
            user_id=user_id,
            ip=ip,
            extra=extra_data,
        )

        with SessionLocal() as db:
            db.add(log_entry)
            db.commit()
