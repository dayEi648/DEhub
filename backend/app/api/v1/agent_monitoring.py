import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.agent_monitoring import (
    AgentEvaluationListResponse,
    AgentEvaluationResponse,
    AgentEvaluationStatsResponse,
    AgentEvaluationTrendResponse,
    AgentSpanListResponse,
    AgentSpanResponse,
    AgentTraceListResponse,
    AgentTraceResponse,
    AgentTraceStatsResponse,
)
from app.crud import agent_evaluation as eval_crud
from app.crud import agent_span as span_crud
from app.crud import agent_trace as trace_crud
from app.services.agent_evaluation_service import AgentEvaluationService

router = APIRouter(prefix="/agent_monitoring", tags=["Agent 监控"])


@router.get("/traces", response_model=AgentTraceListResponse)
def list_traces(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    conversation_id: int | None = Query(default=None),
    user_id: int | None = Query(default=None),
    status: str | None = Query(default=None, pattern=r"^(started|completed|failed)$"),
    is_flagged: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentTraceListResponse:
    """查询 AgentTrace 列表（管理员权限）。"""
    require_admin(current_user)
    traces, total = trace_crud.list_agent_traces(
        db,
        skip=skip,
        limit=limit,
        conversation_id=conversation_id,
        user_id=user_id,
        status=status,
        is_flagged=is_flagged,
    )
    return AgentTraceListResponse(
        items=[AgentTraceResponse.model_validate(t) for t in traces],
        total=total,
    )


@router.get("/traces/{trace_id}", response_model=AgentTraceResponse)
def get_trace(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentTraceResponse:
    """获取单条 AgentTrace 详情（管理员权限）。"""
    require_admin(current_user)
    trace = trace_crud.get_agent_trace_by_trace_id(db, trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace 不存在",
        )
    return AgentTraceResponse.model_validate(trace)


@router.get("/traces/{trace_id}/spans", response_model=AgentSpanListResponse)
def get_trace_spans(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentSpanListResponse:
    """获取某 trace 下的所有 spans（管理员权限）。"""
    require_admin(current_user)
    spans = span_crud.list_agent_spans_by_trace(db, trace_id)
    return AgentSpanListResponse(
        items=[AgentSpanResponse.model_validate(s) for s in spans],
    )


@router.get("/stats", response_model=AgentTraceStatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentTraceStatsResponse:
    """获取 AgentTrace 统计概览（管理员权限）。"""
    require_admin(current_user)
    stats = trace_crud.get_agent_trace_stats(db)
    return AgentTraceStatsResponse(**stats)


# ---------- Phase 3: 质量评估 API ----------


@router.get("/evaluations", response_model=AgentEvaluationListResponse)
def list_evaluations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    dimension: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    max_score: float | None = Query(default=None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentEvaluationListResponse:
    """查询 AgentEvaluation 列表（管理员权限）。"""
    require_admin(current_user)
    items, total = eval_crud.list_agent_evaluations(
        db,
        skip=skip,
        limit=limit,
        dimension=dimension,
        min_score=min_score,
        max_score=max_score,
    )
    return AgentEvaluationListResponse(
        items=[AgentEvaluationResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/evaluations/stats", response_model=AgentEvaluationStatsResponse)
def get_evaluation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentEvaluationStatsResponse:
    """获取评估统计概览（管理员权限）。"""
    require_admin(current_user)
    stats = eval_crud.get_agent_evaluation_stats(db)
    return AgentEvaluationStatsResponse(**stats)


@router.get("/evaluations/trend", response_model=AgentEvaluationTrendResponse)
def get_evaluation_trend(
    days: int = Query(default=7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentEvaluationTrendResponse:
    """获取最近 N 天评估趋势（管理员权限）。"""
    require_admin(current_user)
    items = eval_crud.get_evaluation_trend(db, days=days)
    return AgentEvaluationTrendResponse(items=items)


@router.get("/traces/{trace_id}/evaluations", response_model=AgentEvaluationListResponse)
def get_trace_evaluations(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentEvaluationListResponse:
    """获取某 trace 下的所有评估记录（管理员权限）。"""
    require_admin(current_user)
    items = eval_crud.list_agent_evaluations_by_trace(db, trace_id)
    return AgentEvaluationListResponse(
        items=[AgentEvaluationResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.post("/traces/{trace_id}/evaluate", response_model=AgentEvaluationListResponse)
async def trigger_trace_evaluation(
    trace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentEvaluationListResponse:
    """手动触发对指定 trace 的评估（管理员权限）。"""
    require_admin(current_user)
    trace = trace_crud.get_agent_trace_by_trace_id(db, trace_id)
    if not trace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace 不存在",
        )

    await AgentEvaluationService.evaluate_trace_async(trace_id)

    # 重新读取评估结果返回
    items = eval_crud.list_agent_evaluations_by_trace(db, trace_id)
    return AgentEvaluationListResponse(
        items=[AgentEvaluationResponse.model_validate(i) for i in items],
        total=len(items),
    )


# ---------- Phase 4: 数据导出 ----------


def _serialize_trace(t) -> dict:
    """将 AgentTrace ORM 对象序列化为字典（用于导出）。"""
    return {
        "id": t.id,
        "trace_id": t.trace_id,
        "conversation_id": t.conversation_id,
        "user_id": t.user_id,
        "status": t.status,
        "input_message": t.input_message,
        "output_message": t.output_message,
        "total_tokens": t.total_tokens,
        "prompt_tokens": t.prompt_tokens,
        "completion_tokens": t.completion_tokens,
        "tool_calls_count": t.tool_calls_count,
        "node_steps": t.node_steps,
        "latency_ms": t.latency_ms,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "ended_at": t.ended_at.isoformat() if t.ended_at else None,
        "error_type": t.error_type,
        "error_message": t.error_message,
        "is_flagged": t.is_flagged,
    }


def _serialize_evaluation(e) -> dict:
    """将 AgentEvaluation ORM 对象序列化为字典（用于导出）。"""
    return {
        "id": e.id,
        "trace_id": e.trace_id,
        "conversation_id": e.conversation_id,
        "dimension": e.dimension,
        "score": float(e.score),
        "reason": e.reason,
        "evaluated_at": e.evaluated_at.isoformat() if e.evaluated_at else None,
        "evaluator_model": e.evaluator_model,
    }


@router.get("/traces/export")
def export_traces(
    format: str = Query(default="json", pattern=r"^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出 AgentTrace 数据（JSON 或 CSV）。"""
    require_admin(current_user)
    traces, _ = trace_crud.list_agent_traces(db, skip=0, limit=10000)

    if format == "json":
        import json

        data = [_serialize_trace(t) for t in traces]
        buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        return StreamingResponse(
            buf,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="agent_traces_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            },
        )

    # CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "trace_id", "conversation_id", "user_id", "status", "input_message",
        "output_message", "total_tokens", "tool_calls_count", "node_steps",
        "latency_ms", "started_at", "error_type", "is_flagged",
    ])
    for t in traces:
        writer.writerow([
            t.trace_id,
            t.conversation_id,
            t.user_id,
            t.status,
            (t.input_message or "")[:500],
            (t.output_message or "")[:500],
            t.total_tokens,
            t.tool_calls_count,
            t.node_steps,
            t.latency_ms,
            t.started_at.isoformat() if t.started_at else "",
            t.error_type or "",
            t.is_flagged,
        ])
    bytes_buf = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        bytes_buf,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="agent_traces_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        },
    )


@router.get("/evaluations/export")
def export_evaluations(
    format: str = Query(default="json", pattern=r"^(json|csv)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出 AgentEvaluation 数据（JSON 或 CSV）。"""
    require_admin(current_user)
    items, _ = eval_crud.list_agent_evaluations(db, skip=0, limit=10000)

    if format == "json":
        import json

        data = [_serialize_evaluation(e) for e in items]
        buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        return StreamingResponse(
            buf,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="agent_evaluations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
            },
        )

    # CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "trace_id", "dimension", "score", "reason", "evaluated_at", "evaluator_model",
    ])
    for e in items:
        writer.writerow([
            e.trace_id,
            e.dimension,
            float(e.score),
            (e.reason or "")[:500],
            e.evaluated_at.isoformat() if e.evaluated_at else "",
            e.evaluator_model or "",
        ])
    bytes_buf = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        bytes_buf,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="agent_evaluations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        },
    )
