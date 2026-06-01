from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AgentTraceResponse(BaseModel):
    """单条 AgentTrace 响应。"""

    id: int
    trace_id: str
    conversation_id: int | None
    user_id: int | None
    graph_name: str
    status: str
    input_message: str | None
    output_message: str | None
    total_tokens: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    tool_calls_count: int
    node_steps: int
    latency_ms: int | None
    started_at: datetime
    ended_at: datetime | None
    error_type: str | None
    error_message: str | None
    is_flagged: bool
    meta: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class AgentTraceListResponse(BaseModel):
    """AgentTrace 列表分页响应。"""

    items: list[AgentTraceResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class AgentSpanResponse(BaseModel):
    """单条 AgentSpan 响应。"""

    id: int
    trace_id: str
    parent_span_id: int | None
    span_type: str
    span_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    latency_ms: int | None
    input_data: dict[str, Any] | None
    output_data: dict[str, Any] | None
    error_info: dict[str, Any] | None
    token_usage: dict[str, Any] | None
    meta: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class AgentSpanListResponse(BaseModel):
    """AgentSpan 列表响应。"""

    items: list[AgentSpanResponse]

    model_config = ConfigDict(from_attributes=True)


class AgentTraceStatsResponse(BaseModel):
    """AgentTrace 统计概览。"""

    total: int
    today_count: int
    failed_count: int
    avg_latency_ms: int

    model_config = ConfigDict(from_attributes=True)


class AgentEvaluationResponse(BaseModel):
    """单条 AgentEvaluation 响应。"""

    id: int
    trace_id: str
    conversation_id: int | None
    eval_type: str
    dimension: str
    score: float
    reason: str | None
    evaluated_at: datetime
    evaluator_model: str | None
    meta: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class AgentEvaluationListResponse(BaseModel):
    """AgentEvaluation 列表分页响应。"""

    items: list[AgentEvaluationResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)


class AgentEvaluationStatsResponse(BaseModel):
    """AgentEvaluation 统计概览。"""

    total_evaluations: int
    avg_score: float
    low_score_count: int
    dimension_avgs: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class AgentEvaluationTrendResponse(BaseModel):
    """AgentEvaluation 趋势响应。"""

    items: list[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
