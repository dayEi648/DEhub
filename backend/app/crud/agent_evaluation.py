from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import cast, desc, func, Float
from sqlalchemy.orm import Session

from app.models.agent_evaluation import AgentEvaluation


def create_agent_evaluation(
    db: Session,
    *,
    trace_id: str,
    conversation_id: int | None = None,
    eval_type: str = "auto_llm_judge",
    dimension: str,
    score: float,
    reason: str | None = None,
    evaluator_model: str | None = None,
    metadata: dict | None = None,
) -> AgentEvaluation:
    """创建一条 AgentEvaluation 记录。"""
    eval_record = AgentEvaluation(
        trace_id=trace_id,
        conversation_id=conversation_id,
        eval_type=eval_type,
        dimension=dimension,
        score=score,
        reason=reason,
        evaluator_model=evaluator_model,
        evaluated_at=datetime.now(timezone.utc),
        meta=metadata,
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)
    return eval_record


def batch_create_agent_evaluations(
    db: Session,
    evaluations: list[dict],
) -> list[AgentEvaluation]:
    """批量创建 AgentEvaluation 记录。"""
    created: list[AgentEvaluation] = []
    for eval_data in evaluations:
        record = AgentEvaluation(
            trace_id=eval_data["trace_id"],
            conversation_id=eval_data.get("conversation_id"),
            eval_type=eval_data.get("eval_type", "auto_llm_judge"),
            dimension=eval_data["dimension"],
            score=eval_data["score"],
            reason=eval_data.get("reason"),
            evaluator_model=eval_data.get("evaluator_model"),
            evaluated_at=datetime.now(timezone.utc),
            meta=eval_data.get("metadata"),
        )
        db.add(record)
        created.append(record)
    db.commit()
    for record in created:
        db.refresh(record)
    return created


def list_agent_evaluations_by_trace(
    db: Session,
    trace_id: str,
) -> list[AgentEvaluation]:
    """查询某 trace 下的所有评估记录。"""
    return (
        db.query(AgentEvaluation)
        .filter(AgentEvaluation.trace_id == trace_id)
        .order_by(AgentEvaluation.dimension)
        .all()
    )


def list_agent_evaluations(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    dimension: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
) -> tuple[list[AgentEvaluation], int]:
    """查询 AgentEvaluation 列表，支持筛选。"""
    query = db.query(AgentEvaluation)

    if dimension is not None:
        query = query.filter(AgentEvaluation.dimension == dimension)
    if min_score is not None:
        query = query.filter(AgentEvaluation.score >= min_score)
    if max_score is not None:
        query = query.filter(AgentEvaluation.score <= max_score)

    total = query.count()
    items = (
        query.order_by(desc(AgentEvaluation.evaluated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def get_agent_evaluation_stats(db: Session) -> dict[str, Any]:
    """获取评估统计概览。"""
    total_evals = db.query(AgentEvaluation).count()

    avg_score = (
        db.query(func.avg(cast(AgentEvaluation.score, Float)))
        .scalar()
    ) or 0.0

    low_score_count = (
        db.query(AgentEvaluation)
        .filter(AgentEvaluation.score < 0.5)
        .count()
    )

    # 各维度平均分
    dimension_avgs = (
        db.query(
            AgentEvaluation.dimension,
            func.avg(cast(AgentEvaluation.score, Float)).label("avg_score"),
        )
        .group_by(AgentEvaluation.dimension)
        .all()
    )

    return {
        "total_evaluations": total_evals,
        "avg_score": round(float(avg_score), 2),
        "low_score_count": low_score_count,
        "dimension_avgs": [
            {"dimension": d, "avg_score": round(float(s), 2)}
            for d, s in dimension_avgs
        ],
    }


def get_evaluation_trend(db: Session, days: int = 7) -> list[dict]:
    """获取最近 N 天的每日评估统计。"""
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)

    rows = (
        db.query(
            func.date(AgentEvaluation.evaluated_at).label("date"),
            func.count(AgentEvaluation.id).label("count"),
            func.avg(cast(AgentEvaluation.score, Float)).label("avg_score"),
        )
        .filter(AgentEvaluation.evaluated_at >= since)
        .group_by(func.date(AgentEvaluation.evaluated_at))
        .order_by(func.date(AgentEvaluation.evaluated_at))
        .all()
    )

    return [
        {
            "date": str(r.date),
            "count": r.count,
            "avg_score": round(float(r.avg_score), 2) if r.avg_score else 0.0,
        }
        for r in rows
    ]
