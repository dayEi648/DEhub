from sqlalchemy.orm import Session, joinedload
from app.models.forum_zone import ForumZone
from app.schemas.forum_zone import ForumZoneCreate, ForumZoneUpdate


def get_zone_by_id(db: Session, zone_id: int) -> ForumZone | None:
    """
    根据分区ID获取分区（自动 join 区主信息）
    Args:
        db: 数据库会话
        zone_id: 分区ID
    Returns:
        ForumZone | None: 分区对象或None
    """
    return (
        db.query(ForumZone)
        .options(joinedload(ForumZone.manager))
        .filter(ForumZone.id == zone_id)
        .first()
    )


def get_zone_by_slug(db: Session, slug: str) -> ForumZone | None:
    """
    根据分区 slug 获取分区（自动 join 区主信息）
    Args:
        db: 数据库会话
        slug: 分区 slug
    Returns:
        ForumZone | None: 分区对象或None
    """
    return (
        db.query(ForumZone)
        .options(joinedload(ForumZone.manager))
        .filter(ForumZone.slug == slug)
        .first()
    )


def get_all_zones(db: Session) -> list[ForumZone]:
    """
    获取所有分区（自动 join 区主信息）
    Args:
        db: 数据库会话
    Returns:
        list[ForumZone]: 分区列表
    """
    return db.query(ForumZone).options(joinedload(ForumZone.manager)).all()


def create_zone(db: Session, zone_in: ForumZoneCreate, manager_id: int) -> ForumZone:
    """
    创建分区
    Args:
        db: 数据库会话
        zone_in: 分区创建请求
        manager_id: 分区管理员用户ID
    Returns:
        ForumZone: 分区对象
    """
    db_zone = ForumZone(**zone_in.model_dump(exclude={"manager_id"}), manager_id=manager_id)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def update_zone(
    db: Session, db_zone: ForumZone, zone_in: ForumZoneUpdate
) -> ForumZone:
    """
    更新分区
    Args:
        db: 数据库会话
        db_zone: 分区对象
        zone_in: 分区更新请求
    Returns:
        ForumZone: 分区对象
    """
    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def delete_zone(db: Session, zone_id: int) -> int:
    """
    删除分区
    Args:
        db: 数据库会话
        zone_id: 分区ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(ForumZone)
        .filter(ForumZone.id == zone_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def update_zones_manager_by_old_manager(
    db: Session, old_manager_id: int, new_manager_id: int
) -> int:
    """
    批量将指定区主管理的分区的 manager_id 转移给新区主
    Args:
        db: 数据库会话
        old_manager_id: 原区主用户ID
        new_manager_id: 新区主用户ID
    Returns:
        int: 更新行数
    """
    result = (
        db.query(ForumZone)
        .filter(ForumZone.manager_id == old_manager_id)
        .update({"manager_id": new_manager_id}, synchronize_session=False)
    )
    db.commit()
    return result


