from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SystemLogResponse(BaseModel):
    """单条系统日志响应"""

    id: int
    level: str
    module: str | None = None
    message: str
    exception: str | None = None
    trace_id: str | None = None
    user_id: int | None = None
    ip: str | None = None
    extra: dict[str, Any] | None = None
    is_resolved: bool
    resolved_at: datetime | None = None
    resolved_by: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemLogListResponse(BaseModel):
    """系统日志列表分页响应"""

    items: list[SystemLogResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class SystemLogStatsResponse(BaseModel):
    """系统日志统计概览"""

    total: int
    total_unresolved: int
    warn_count: int
    error_count: int
    critical_count: int


class BatchResolveRequest(BaseModel):
    """批量标记已处理请求"""

    ids: list[int] = Field(min_length=1)


class BatchResolveResponse(BaseModel):
    """批量标记已处理响应。"""

    resolved_count: int
