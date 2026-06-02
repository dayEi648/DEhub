from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.content_moderation_record import ContentModerationRecord


def create_moderation_record(
    db: Session,
    *,
    task_id: str,
    target_type: str,
    target_id: int,
    target_version: str,
    trigger_action: str,
    original_snapshot: dict,
    created_by_user_id: int | None = None,
) -> ContentModerationRecord:
    """创建一条待审核记录。"""
    record = ContentModerationRecord(
        task_id=task_id,
        target_type=target_type,
        target_id=target_id,
        target_version=target_version,
        trigger_action=trigger_action,
        status="pending",
        original_snapshot=original_snapshot,
        created_by_user_id=created_by_user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_moderation_record_by_id(
    db: Session, record_id: int
) -> ContentModerationRecord | None:
    """通过 ID 查询单条审核记录。"""
    return (
        db.query(ContentModerationRecord)
        .filter(ContentModerationRecord.id == record_id)
        .first()
    )


def get_moderation_record_by_task_id(
    db: Session, task_id: str
) -> ContentModerationRecord | None:
    """通过 task_id 查询单条审核记录。"""
    return (
        db.query(ContentModerationRecord)
        .filter(ContentModerationRecord.task_id == task_id)
        .first()
    )


def list_moderation_records(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    target_type: str | None = None,
    risk_level: str | None = None,
    user_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> tuple[list[ContentModerationRecord], int]:
    """分页查询审核记录，支持多维筛选。"""
    query = db.query(ContentModerationRecord)

    if status is not None:
        query = query.filter(ContentModerationRecord.status == status)
    if target_type is not None:
        query = query.filter(ContentModerationRecord.target_type == target_type)
    if risk_level is not None:
        query = query.filter(ContentModerationRecord.risk_level == risk_level)
    if user_id is not None:
        query = query.filter(ContentModerationRecord.created_by_user_id == user_id)
    if start_time is not None:
        query = query.filter(ContentModerationRecord.created_at >= start_time)
    if end_time is not None:
        query = query.filter(ContentModerationRecord.created_at <= end_time)

    total = query.count()
    items = (
        query.order_by(desc(ContentModerationRecord.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_moderation_record(
    db: Session,
    record_id: int,
    **kwargs,
) -> ContentModerationRecord | None:
    """更新审核记录状态与结果字段。"""
    record = get_moderation_record_by_id(db, record_id)
    if not record:
        return None

    allowed = {
        "status",
        "trace_id",
        "task_id",
        "risk_level",
        "categories",
        "moderation_result",
        "action_plan",
        "action_result",
        "model_name",
        "error_type",
        "error_message",
        "started_at",
        "finished_at",
        "trigger_action",
    }
    for key, value in kwargs.items():
        if key in allowed and hasattr(record, key):
            setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


def get_moderation_stats(db: Session) -> dict:
    """获取审核统计概览。"""
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    total = db.query(ContentModerationRecord).count()
    today_count = (
        db.query(ContentModerationRecord)
        .filter(ContentModerationRecord.created_at >= today)
        .count()
    )
    failed_count = (
        db.query(ContentModerationRecord)
        .filter(
            ContentModerationRecord.status.in_(
                ["review_failed", "action_failed"]
            )
        )
        .count()
    )
    blocked_count = (
        db.query(ContentModerationRecord)
        .filter(ContentModerationRecord.status == "blocked")
        .count()
    )
    avg_latency = db.query(
        func.avg(
            func.extract(
                "epoch",
                ContentModerationRecord.finished_at
                - ContentModerationRecord.started_at,
            )
            * 1000
        )
    ).scalar()

    return {
        "total": total,
        "today_count": today_count,
        "failed_count": failed_count,
        "blocked_count": blocked_count,
        "avg_latency_ms": int(avg_latency) if avg_latency is not None else None,
    }


def get_pending_or_running_records(
    db: Session, older_than_minutes: int = 30
) -> list[ContentModerationRecord]:
    """获取长时间处于 pending 或 running 状态的记录，用于超时检测。"""
    threshold = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    return (
        db.query(ContentModerationRecord)
        .filter(
            ContentModerationRecord.status.in_(["pending", "running"]),
            ContentModerationRecord.created_at <= threshold,
        )
        .all()
    )
