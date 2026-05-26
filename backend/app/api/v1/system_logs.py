from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.permissions import require_admin
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.system_log import (
    BatchResolveResponse,
    BatchResolveRequest,
    SystemLogListResponse,
    SystemLogResponse,
    SystemLogStatsResponse,
)
from app.services.system_log_service import SystemLogService

router = APIRouter(prefix="/system_logs", tags=["系统日志监控"])


@router.get("/", response_model=SystemLogListResponse)
def list_system_logs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    level: str | None = Query(
        default=None, pattern=r"^(WARN|ERROR|CRITICAL)$"
    ),
    is_resolved: bool | None = Query(default=None),
    module: str | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SystemLogListResponse:
    """
    查询系统告警日志列表（管理员及以上权限）。

    支持按日志级别、是否已处理、模块名、时间范围筛选，默认按时间倒序排列。
    """
    require_admin(current_user)
    logs, total = SystemLogService(db).list_logs(
        skip=skip,
        limit=limit,
        level=level,
        is_resolved=is_resolved,
        module=module,
        created_after=created_after,
        created_before=created_before,
    )
    return SystemLogListResponse(items=logs, total=total)


@router.get("/stats", response_model=SystemLogStatsResponse)
def get_system_log_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SystemLogStatsResponse:
    """
    获取日志统计概览（管理员及以上权限）。
    """
    require_admin(current_user)
    stats = SystemLogService(db).get_stats()
    return SystemLogStatsResponse(**stats)


@router.post("/batch_resolve", response_model=BatchResolveResponse)
def batch_resolve_system_logs(
    req: BatchResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchResolveResponse:
    """
    批量标记日志为已处理（管理员及以上权限）。

    Returns:
        {"resolved_count": 实际更新的条数}
    """
    require_admin(current_user)
    count = SystemLogService(db).batch_resolve_logs(
        req.ids, resolved_by=current_user.id
    )
    return BatchResolveResponse(resolved_count=count)


@router.get("/{log_id}", response_model=SystemLogResponse)
def get_system_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SystemLogResponse:
    """
    查看单条日志详情（管理员及以上权限）。
    """
    require_admin(current_user)
    log = SystemLogService(db).get_log(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在"
        )
    return log


@router.post("/{log_id}/resolve", response_model=SystemLogResponse)
def resolve_system_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SystemLogResponse:
    """
    将指定日志标记为已处理（管理员及以上权限）。
    """
    require_admin(current_user)
    log = SystemLogService(db).resolve_log(log_id, resolved_by=current_user.id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在"
        )
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_system_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除指定日志（管理员及以上权限）。
    """
    require_admin(current_user)
    deleted = SystemLogService(db).delete_log(log_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="日志不存在"
        )
    return None
