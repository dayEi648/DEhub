from datetime import datetime, timezone

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.agent_trace import AgentTrace


def create_agent_trace(
    db: Session,
    *,
    trace_id: str,
    conversation_id: int | None = None,
    user_id: int | None = None,
    graph_name: str = "chat_agent",
    status: str = "started",
    input_message: str | None = None,
    output_message: str | None = None,
    total_tokens: int | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    tool_calls_count: int = 0,
    node_steps: int = 0,
    latency_ms: int | None = None,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> AgentTrace:
    """创建一条 AgentTrace 记录。"""
    trace = AgentTrace(
        trace_id=trace_id,
        conversation_id=conversation_id,
        user_id=user_id,
        graph_name=graph_name,
        status=status,
        input_message=input_message,
        output_message=output_message,
        total_tokens=total_tokens,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        tool_calls_count=tool_calls_count,
        node_steps=node_steps,
        latency_ms=latency_ms,
        started_at=started_at or datetime.now(timezone.utc),
        ended_at=ended_at,
        error_type=error_type,
        error_message=error_message,
        meta=metadata,
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return trace


def update_agent_trace(
    db: Session,
    trace_id: str,
    **kwargs,
) -> AgentTrace | None:
    """通过 trace_id 更新 AgentTrace。"""
    trace = db.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).first()
    if not trace:
        return None
    allowed = {
        "status",
        "output_message",
        "total_tokens",
        "prompt_tokens",
        "completion_tokens",
        "tool_calls_count",
        "node_steps",
        "latency_ms",
        "ended_at",
        "error_type",
        "error_message",
        "metadata",
        "is_flagged",
    }
    attr_map = {"metadata": "meta"}
    for key, value in kwargs.items():
        if key in allowed:
            attr = attr_map.get(key, key)
            if hasattr(trace, attr):
                setattr(trace, attr, value)
    db.commit()
    db.refresh(trace)
    return trace


def get_agent_trace_by_trace_id(
    db: Session, trace_id: str
) -> AgentTrace | None:
    """通过 trace_id 查询单条记录。"""
    return db.query(AgentTrace).filter(AgentTrace.trace_id == trace_id).first()


def list_agent_traces(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    conversation_id: int | None = None,
    user_id: int | None = None,
    status: str | None = None,
    is_flagged: bool | None = None,
) -> tuple[list[AgentTrace], int]:
    """查询 AgentTrace 列表，支持筛选。"""
    query = db.query(AgentTrace)

    if conversation_id is not None:
        query = query.filter(AgentTrace.conversation_id == conversation_id)
    if user_id is not None:
        query = query.filter(AgentTrace.user_id == user_id)
    if status is not None:
        query = query.filter(AgentTrace.status == status)
    if is_flagged is not None:
        query = query.filter(AgentTrace.is_flagged == is_flagged)

    total = query.count()
    traces = (
        query.order_by(desc(AgentTrace.started_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return traces, total


def get_agent_trace_stats(db: Session) -> dict[str, int]:
    """获取基础统计。"""
    from sqlalchemy import func

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    total = db.query(AgentTrace).count()
    today_count = (
        db.query(AgentTrace)
        .filter(AgentTrace.started_at >= today)
        .count()
    )
    failed_count = (
        db.query(AgentTrace)
        .filter(AgentTrace.status == "failed")
        .count()
    )
    avg_latency = db.query(func.avg(AgentTrace.latency_ms)).scalar() or 0

    return {
        "total": total,
        "today_count": today_count,
        "failed_count": failed_count,
        "avg_latency_ms": int(avg_latency),
    }
