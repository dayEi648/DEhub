import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.crud import content_moderation as cm_crud
from app.models.user import User
from app.schemas.content_moderation import (
    ContentModerationRecordListResponse,
    ContentModerationRecordResponse,
    ContentModerationRetryResponse,
    ContentModerationStatsResponse,
)
from app.services.content_moderation_service import ContentModerationService

router = APIRouter(prefix="/content_moderation", tags=["内容审核"])

# ------------------------------------------------------------------
# 列表查询
# ------------------------------------------------------------------

@router.get("/records", response_model=ContentModerationRecordListResponse)
def list_moderation_records(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(
        default=None,
        pattern=r"^(pending|running|passed|blocked|action_failed|review_failed|stale)$",
    ),
    target_type: str | None = Query(
        default=None,
        pattern=r"^(user|blog_post|forum_zone|forum_post|forum_reply|comment)$",
    ),
    risk_level: str | None = Query(
        default=None,
        pattern=r"^(none|low|medium|high)$",
    ),
    user_id: int | None = Query(default=None, ge=1),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentModerationRecordListResponse:
    """分页查询内容审核记录（管理员及以上权限）。

    支持按状态、对象类型、风险等级、用户ID、时间范围筛选，默认按时间倒序排列。
    """
    require_admin(current_user)
    items, total = cm_crud.list_moderation_records(
        db,
        skip=skip,
        limit=limit,
        status=status,
        target_type=target_type,
        risk_level=risk_level,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
    )
    return ContentModerationRecordListResponse(
        items=[ContentModerationRecordResponse.model_validate(r) for r in items],
        total=total,
    )


# ------------------------------------------------------------------
# 统计概览
# ------------------------------------------------------------------

@router.get("/stats", response_model=ContentModerationStatsResponse)
def get_moderation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentModerationStatsResponse:
    """获取内容审核统计概览（管理员及以上权限）。

    返回总量、今日、失败、不通过及平均耗时。
    """
    require_admin(current_user)
    stats = cm_crud.get_moderation_stats(db)
    return ContentModerationStatsResponse(**stats)


# ------------------------------------------------------------------
# 数据导出（必须在动态路由 /records/{record_id} 之前注册）
# ------------------------------------------------------------------

def _serialize_record(r) -> dict:
    """将 ContentModerationRecord ORM 对象序列化为字典（用于导出）。"""
    return {
        "id": r.id,
        "task_id": r.task_id,
        "trace_id": r.trace_id,
        "target_type": r.target_type,
        "target_id": r.target_id,
        "target_version": r.target_version,
        "trigger_action": r.trigger_action,
        "status": r.status,
        "risk_level": r.risk_level,
        "categories": r.categories,
        "original_snapshot": r.original_snapshot,
        "moderation_result": r.moderation_result,
        "action_plan": r.action_plan,
        "action_result": r.action_result,
        "model_name": r.model_name,
        "error_type": r.error_type,
        "error_message": r.error_message,
        "created_by_user_id": r.created_by_user_id,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }


@router.get("/records/export")
def export_moderation_records(
    format: str = Query(default="json", pattern=r"^(json|csv)$"),
    status: str | None = Query(
        default=None,
        pattern=r"^(pending|running|passed|blocked|action_failed|review_failed|stale)$",
    ),
    target_type: str | None = Query(
        default=None,
        pattern=r"^(user|blog_post|forum_zone|forum_post|forum_reply|comment)$",
    ),
    risk_level: str | None = Query(
        default=None,
        pattern=r"^(none|low|medium|high)$",
    ),
    user_id: int | None = Query(default=None, ge=1),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出审核记录数据（JSON 或 CSV，管理员及以上权限）。

    原始敏感内容仅管理员可见，导出受同级权限控制。
    支持全量筛选条件，默认导出最多 10000 条。
    """
    require_admin(current_user)

    items, _ = cm_crud.list_moderation_records(
        db,
        skip=0,
        limit=10000,
        status=status,
        target_type=target_type,
        risk_level=risk_level,
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if format == "json":
        data = [_serialize_record(r) for r in items]
        buf = io.BytesIO(
            json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        )
        return StreamingResponse(
            buf,
            media_type="application/json",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="content_moderation_{timestamp}.json"'
                )
            },
        )

    # CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "task_id", "trace_id", "target_type", "target_id",
        "target_version", "trigger_action", "status", "risk_level",
        "categories", "model_name", "error_type", "error_message",
        "created_by_user_id", "created_at", "started_at", "finished_at",
    ])
    for r in items:
        writer.writerow([
            r.id,
            r.task_id,
            r.trace_id or "",
            r.target_type,
            r.target_id,
            r.target_version,
            r.trigger_action,
            r.status,
            r.risk_level,
            ",".join(r.categories) if r.categories else "",
            r.model_name or "",
            r.error_type or "",
            (r.error_message or "")[:500],
            r.created_by_user_id or "",
            r.created_at.isoformat() if r.created_at else "",
            r.started_at.isoformat() if r.started_at else "",
            r.finished_at.isoformat() if r.finished_at else "",
        ])

    bytes_buf = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        bytes_buf,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="content_moderation_{timestamp}.csv"'
            )
        },
    )


# ------------------------------------------------------------------
# 单条详情
# ------------------------------------------------------------------

@router.get("/records/{record_id}", response_model=ContentModerationRecordResponse)
def get_moderation_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentModerationRecordResponse:
    """获取单条审核记录详情（管理员及以上权限）。

    包含 original_snapshot、moderation_result、action_plan、action_result 完整数据。
    """
    require_admin(current_user)
    record = cm_crud.get_moderation_record_by_id(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在",
        )
    return ContentModerationRecordResponse.model_validate(record)


# ------------------------------------------------------------------
# 重试审核
# ------------------------------------------------------------------

@router.post("/records/{record_id}/retry", response_model=ContentModerationRetryResponse)
def retry_moderation_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContentModerationRetryResponse:
    """重试审核记录（管理员及以上权限）。

    仅允许对 review_failed / action_failed / stale 状态的记录进行重试。
    重试会重置记录为 pending 并重新调度后台审核任务。
    """
    require_admin(current_user)
    record = cm_crud.get_moderation_record_by_id(db, record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在",
        )

    if record.status not in ("review_failed", "action_failed", "stale"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"记录状态不允许重试: {record.status}",
        )

    service = ContentModerationService(db)
    try:
        new_record = service.retry(record_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return ContentModerationRetryResponse(
        id=new_record.id,
        task_id=new_record.task_id,
        status=new_record.status,
        message="审核任务已重新调度",
    )
