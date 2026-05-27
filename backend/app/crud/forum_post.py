from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from app.models.forum_post import ForumPost
from app.schemas.forum_post import ForumPostCreate, ForumPostUpdate


def get_post_by_id(db: Session, post_id: int) -> ForumPost | None:
    return (
        db.query(ForumPost)
        .options(joinedload(ForumPost.user))
        .filter(ForumPost.id == post_id)
        .first()
    )


def get_posts(
    db: Session,
    zone_id: int | None = None,
    sort_by: str = "created",
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[ForumPost], int]:
    query = db.query(ForumPost).options(joinedload(ForumPost.user))

    if zone_id is not None:
        query = query.filter(ForumPost.zone_id == zone_id)

    if sort_by == "view":
        query = query.order_by(desc(ForumPost.view_count), desc(ForumPost.created_at))
    else:
        query = query.order_by(desc(ForumPost.created_at))

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def create_post(db: Session, post_in: ForumPostCreate, user_id: int) -> ForumPost:
    db_post = ForumPost(**post_in.model_dump(), user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(
    db: Session, db_post: ForumPost, post_in: ForumPostUpdate
) -> ForumPost:
    update_data = post_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int, auto_commit: bool = True) -> int:
    result = (
        db.query(ForumPost)
        .filter(ForumPost.id == post_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def get_post_ids_by_user_id(db: Session, user_id: int) -> list[int]:
    rows = db.query(ForumPost.id).filter(ForumPost.user_id == user_id).all()
    return [row[0] for row in rows]


def increment_post_view_count(db: Session, post_id: int) -> int:
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"view_count": ForumPost.view_count + 1},
        synchronize_session=False,
    )
    db.commit()
    return result


def increment_reply_count(db: Session, post_id: int, auto_commit: bool = True) -> int:
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"reply_count": ForumPost.reply_count + 1},
        synchronize_session=False,
    )
    if auto_commit:
        db.commit()
    return result


def decrement_reply_count(db: Session, post_id: int, auto_commit: bool = True) -> int:
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"reply_count": func.greatest(ForumPost.reply_count - 1, 0)},
        synchronize_session=False,
    )
    if auto_commit:
        db.commit()
    return result
