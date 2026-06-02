from datetime import datetime, timezone

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.system_log import SystemLog


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    level: str | None = None,
    is_resolved: bool | None = None,
    module: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> tuple[list[SystemLog], int]:
    query = db.query(SystemLog)

    if level:
        query = query.filter(SystemLog.level == level)
    if is_resolved is not None:
        query = query.filter(SystemLog.is_resolved == is_resolved)
    if module:
        escaped_module = module.replace("%", r"\%").replace("_", r"\_")
        query = query.filter(SystemLog.module.ilike(f"%{escaped_module}%", escape="\\"))
    if created_after:
        query = query.filter(SystemLog.created_at >= created_after)
    if created_before:
        query = query.filter(SystemLog.created_at <= created_before)

    total = query.count()
    logs = (
        query.order_by(desc(SystemLog.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs, total


def get_log_by_id(db: Session, log_id: int) -> SystemLog | None:
    """根据 ID 获取单条日志。"""
    return db.query(SystemLog).filter(SystemLog.id == log_id).first()


def resolve_log(db: Session, log_id: int, resolved_by: int) -> SystemLog | None:
    log = db.query(SystemLog).filter(SystemLog.id == log_id).first()
    if not log:
        return None

    log.is_resolved = True
    log.resolved_at = datetime.now(timezone.utc)
    log.resolved_by = resolved_by
    db.commit()
    db.refresh(log)
    return log


def batch_resolve_logs(
    db: Session, log_ids: list[int], resolved_by: int
) -> int:
    now = datetime.now(timezone.utc)
    result = (
        db.query(SystemLog)
        .filter(SystemLog.id.in_(log_ids))
        .update(
            {
                SystemLog.is_resolved: True,
                SystemLog.resolved_at: now,
                SystemLog.resolved_by: resolved_by,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return result


def delete_log(db: Session, log_id: int) -> bool:
    result = (
        db.query(SystemLog)
        .filter(SystemLog.id == log_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0


def get_stats(db: Session) -> dict[str, int]:
    total = db.query(SystemLog).count()
    total_unresolved = (
        db.query(SystemLog).filter(SystemLog.is_resolved == False).count()
    )

    level_counts = {
        row[0]: row[1]
        for row in db.query(SystemLog.level, func.count(SystemLog.id))
        .group_by(SystemLog.level)
        .all()
    }

    return {
        "total": total,
        "total_unresolved": total_unresolved,
        "warn_count": level_counts.get("WARN", 0),
        "error_count": level_counts.get("ERROR", 0),
        "critical_count": level_counts.get("CRITICAL", 0),
    }
