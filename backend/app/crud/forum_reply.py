from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from app.models.forum_reply import ForumReply
from app.models.user_forum_reply_like import UserForumReplyLike
from app.schemas.forum_reply import ForumReplyCreate


def get_reply_by_id(db: Session, reply_id: int) -> ForumReply | None:
    return (
        db.query(ForumReply)
        .options(joinedload(ForumReply.user))
        .filter(ForumReply.id == reply_id)
        .first()
    )


def get_replies_by_post_id(
    db: Session,
    post_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[ForumReply], int]:
    query = db.query(ForumReply).filter(ForumReply.post_id == post_id)
    total = query.count()
    items = (
        query.options(joinedload(ForumReply.user))
        .order_by(desc(ForumReply.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def create_reply(
    db: Session,
    reply_in: ForumReplyCreate,
    user_id: int,
    auto_commit: bool = True,
) -> ForumReply:
    db_reply = ForumReply(**reply_in.model_dump(), user_id=user_id)
    db.add(db_reply)
    if auto_commit:
        db.commit()
    else:
        db.flush()
    db.refresh(db_reply)
    return db_reply


def get_all_replies_by_post_id(db: Session, post_id: int) -> list[ForumReply]:
    return db.query(ForumReply).filter(ForumReply.post_id == post_id).all()


def delete_reply(db: Session, reply_id: int, auto_commit: bool = True) -> int:
    result = (
        db.query(ForumReply)
        .filter(ForumReply.id == reply_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def delete_replies_by_post_ids(
    db: Session, post_ids: list[int], auto_commit: bool = True
) -> int:
    if not post_ids:
        return 0
    result = (
        db.query(ForumReply)
        .filter(ForumReply.post_id.in_(post_ids))
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def delete_replies_by_user_id(
    db: Session, user_id: int, auto_commit: bool = True
) -> int:
    result = (
        db.query(ForumReply)
        .filter(ForumReply.user_id == user_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


# ---------- 回复点赞相关 ----------


def get_user_forum_reply_like(
    db: Session, reply_id: int, user_id: int
) -> UserForumReplyLike | None:
    return (
        db.query(UserForumReplyLike)
        .filter(
            UserForumReplyLike.reply_id == reply_id,
            UserForumReplyLike.user_id == user_id,
        )
        .first()
    )


def create_user_forum_reply_like(
    db: Session, reply_id: int, user_id: int, auto_commit: bool = True
) -> UserForumReplyLike:
    db_like = UserForumReplyLike(reply_id=reply_id, user_id=user_id)
    db.add(db_like)
    if auto_commit:
        db.commit()
    db.refresh(db_like)
    return db_like


def delete_user_forum_reply_like(
    db: Session, reply_id: int, user_id: int, auto_commit: bool = True
) -> int:
    result = (
        db.query(UserForumReplyLike)
        .filter(
            UserForumReplyLike.reply_id == reply_id,
            UserForumReplyLike.user_id == user_id,
        )
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def get_user_liked_reply_ids(
    db: Session,
    user_id: int,
    reply_ids: list[int],
) -> set[int]:
    if not reply_ids:
        return set()
    rows = (
        db.query(UserForumReplyLike.reply_id)
        .filter(
            UserForumReplyLike.user_id == user_id,
            UserForumReplyLike.reply_id.in_(reply_ids),
        )
        .all()
    )
    return {row[0] for row in rows}


def delete_forum_reply_likes_by_reply_ids(
    db: Session, reply_ids: list[int], auto_commit: bool = True
) -> int:
    if not reply_ids:
        return 0
    result = (
        db.query(UserForumReplyLike)
        .filter(UserForumReplyLike.reply_id.in_(reply_ids))
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def delete_forum_reply_likes_by_user_id(
    db: Session, user_id: int, auto_commit: bool = True
) -> int:
    result = (
        db.query(UserForumReplyLike)
        .filter(UserForumReplyLike.user_id == user_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result
