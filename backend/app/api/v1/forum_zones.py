from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.forum_zone import (
    ForumZoneCreate,
    ForumZoneUpdate,
    ForumZoneResponse,
)
from app.services.forum_zone_service import ForumZoneService

router = APIRouter(prefix="/forum_zones", tags=["论坛分区管理"])


@router.post("/", response_model=ForumZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone_in: ForumZoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumZoneResponse:
    """创建分区（管理员及以上）。"""
    service = ForumZoneService(db)
    return service.create_zone(zone_in, current_user)


@router.get("/", response_model=List[ForumZoneResponse])
def list_zones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ForumZoneResponse]:
    """查询所有分区列表。"""
    service = ForumZoneService(db)
    return service.list_zones()


@router.get("/{zone_id}", response_model=ForumZoneResponse)
def get_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumZoneResponse:
    """根据 ID 查询分区详情。"""
    service = ForumZoneService(db)
    return service.get_zone(zone_id)


@router.get("/by-slug/{slug}", response_model=ForumZoneResponse)
def get_zone_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumZoneResponse:
    """根据 slug 查询分区详情（SEO 友好）。"""
    service = ForumZoneService(db)
    return service.get_zone_by_slug(slug)


@router.put("/{zone_id}", response_model=ForumZoneResponse)
def update_zone(
    zone_id: int,
    zone_in: ForumZoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ForumZoneResponse:
    """编辑分区（管理员及以上或区主）。"""
    service = ForumZoneService(db)
    return service.update_zone(zone_id, zone_in, current_user)


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """删除分区（管理员及以上，若分区下还有帖子将返回 400）。"""
    service = ForumZoneService(db)
    service.delete_zone(zone_id, current_user)
    return None
