from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class FlaggedSpan(BaseModel):
    """模型标出的敏感文本片段。"""

    field: str
    text: str
    start: int
    end: int
    category: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class ContentModerationRecordResponse(BaseModel):
    """单条内容审核记录响应。"""

    id: int
    task_id: str
    trace_id: str | None
    target_type: str
    target_id: int
    target_version: str
    trigger_action: str
    status: str
    risk_level: str
    categories: list[str] | None
    original_snapshot: dict[str, Any]
    moderation_result: dict[str, Any] | None
    action_plan: dict[str, Any] | None
    action_result: dict[str, Any] | None
    model_name: str | None
    error_type: str | None
    error_message: str | None
    created_by_user_id: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ContentModerationRecordListResponse(BaseModel):
    """内容审核记录分页列表响应。"""

    items: list[ContentModerationRecordResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class ContentModerationStatsResponse(BaseModel):
    """内容审核统计概览响应。"""

    total: int
    today_count: int
    failed_count: int
    blocked_count: int
    avg_latency_ms: int | None

    model_config = ConfigDict(from_attributes=True)


class ContentModerationRetryResponse(BaseModel):
    """审核重试操作响应。"""

    id: int
    task_id: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class ModerationAgentOutput(BaseModel):
    """审核 Agent 结构化输出（用于解析 LLM 返回的 JSON）。"""

    verdict: str
    risk_level: str
    categories: list[str]
    reason: str
    flagged_spans: list[FlaggedSpan]
    suggested_action: str

    model_config = ConfigDict(from_attributes=True)
