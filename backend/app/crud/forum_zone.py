from sqlalchemy.orm import Session, joinedload
from app.models.forum_zone import ForumZone
from app.schemas.forum_zone import ForumZoneCreate, ForumZoneUpdate


def get_zone_by_id(db: Session, zone_id: int) -> ForumZone | None:
    return (
        db.query(ForumZone)
        .options(joinedload(ForumZone.manager))
        .filter(ForumZone.id == zone_id)
        .first()
    )


def get_zone_by_slug(db: Session, slug: str) -> ForumZone | None:
    return (
        db.query(ForumZone)
        .options(joinedload(ForumZone.manager))
        .filter(ForumZone.slug == slug)
        .first()
    )


def get_all_zones(db: Session) -> list[ForumZone]:
    return db.query(ForumZone).options(joinedload(ForumZone.manager)).all()


def create_zone(db: Session, zone_in: ForumZoneCreate, manager_id: int) -> ForumZone:
    db_zone = ForumZone(**zone_in.model_dump(exclude={"manager_id"}), manager_id=manager_id)
    db.add(db_zone)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def update_zone(
    db: Session, db_zone: ForumZone, zone_in: ForumZoneUpdate
) -> ForumZone:
    update_data = zone_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_zone, field, value)
    db.commit()
    db.refresh(db_zone)
    return db_zone


def delete_zone(db: Session, zone_id: int) -> int:
    result = (
        db.query(ForumZone)
        .filter(ForumZone.id == zone_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def update_zones_manager_by_old_manager(
    db: Session, old_manager_id: int, new_manager_id: int, auto_commit: bool = True
) -> int:
    result = (
        db.query(ForumZone)
        .filter(ForumZone.manager_id == old_manager_id)
        .update({"manager_id": new_manager_id}, synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result
