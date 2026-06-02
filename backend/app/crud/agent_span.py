from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.agent_span import AgentSpan


def batch_create_agent_spans(
    db: Session,
    trace_id: str,
    spans: list[dict],
) -> list[AgentSpan]:
    """批量创建 AgentSpan 记录。

    Args:
        db: 数据库 Session
        trace_id: 所属 trace_id
        spans: span 数据列表，每项为 dict，包含 span 各字段

    Returns:
        创建的 AgentSpan 对象列表
    """
    created: list[AgentSpan] = []
    tmp_to_span: dict[str, AgentSpan] = {}
    for span_data in spans:
        span = AgentSpan(
            trace_id=trace_id,
            parent_span_id=span_data.get("parent_span_id"),
            span_type=span_data.get("span_type", "unknown"),
            span_name=span_data.get("span_name", "unknown"),
            status=span_data.get("status", "completed"),
            started_at=span_data.get("started_at") or datetime.now(timezone.utc),
            ended_at=span_data.get("ended_at"),
            latency_ms=span_data.get("latency_ms"),
            input_data=span_data.get("input_data"),
            output_data=span_data.get("output_data"),
            error_info=span_data.get("error_info"),
            token_usage=span_data.get("token_usage"),
            meta=span_data.get("metadata"),
        )
        db.add(span)
        created.append(span)
        tmp_span_id = span_data.get("tmp_span_id")
        if tmp_span_id:
            tmp_to_span[tmp_span_id] = span

    db.flush()

    for span, span_data in zip(created, spans, strict=False):
        parent_tmp_span_id = span_data.get("parent_tmp_span_id")
        if parent_tmp_span_id and parent_tmp_span_id in tmp_to_span:
            span.parent_span_id = tmp_to_span[parent_tmp_span_id].id

    db.commit()
    for span in created:
        db.refresh(span)
    return created


def list_agent_spans_by_trace(
    db: Session,
    trace_id: str,
) -> list[AgentSpan]:
    """查询某 trace 下的所有 spans，按开始时间正序排列。"""
    return (
        db.query(AgentSpan)
        .filter(AgentSpan.trace_id == trace_id)
        .order_by(AgentSpan.started_at)
        .all()
    )
