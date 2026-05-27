from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.comment import Comment
from app.models.user_comment_like import UserCommentLike
from app.schemas.comment import CommentCreate


def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    return (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter(Comment.id == comment_id)
        .first()
    )


def get_comments(
    db: Session,
    target_type: str,
    target_id: int,
    parent_id: int | None = None,
    is_nested: bool | None = None,
    nested_parent_id: int | None = None,
    sort_by: str = "time",
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Comment], int]:
    query = db.query(Comment).filter(
        Comment.target_type == target_type,
        Comment.target_id == target_id,
    )

    if parent_id is not None:
        if parent_id == 0:
            query = query.filter(Comment.parent_id.is_(None))
        else:
            query = query.filter(Comment.parent_id == parent_id)

    if is_nested is not None:
        query = query.filter(Comment.is_nested == is_nested)

    if nested_parent_id is not None:
        query = query.filter(Comment.nested_parent_id == nested_parent_id)

    if sort_by == "hot":
        query = query.order_by(desc(Comment.likecount), desc(Comment.created_at))
    elif sort_by == "time_asc":
        query = query.order_by(Comment.created_at)
    else:
        query = query.order_by(desc(Comment.created_at))

    total = query.count()
    items = (
        query.options(joinedload(Comment.user))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def get_comments_by_parent_id(
    db: Session, parent_id: int
) -> list[Comment]:
    return db.query(Comment).filter(Comment.parent_id == parent_id).all()


def create_comment(db: Session, comment_in: CommentCreate, user_id: int) -> Comment:
    db_comment = Comment(
        target_type=comment_in.target_type,
        target_id=comment_in.target_id,
        parent_id=comment_in.parent_id,
        user_id=user_id,
        content=comment_in.content,
        is_nested=comment_in.is_nested,
        nested_parent_id=comment_in.nested_parent_id,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: int) -> int:
    result = (
        db.query(Comment)
        .filter(Comment.id == comment_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def delete_comments_by_ids(
    db: Session, comment_ids: list[int], auto_commit: bool = True
) -> int:
    if not comment_ids:
        return 0
    result = (
        db.query(Comment)
        .filter(Comment.id.in_(comment_ids))
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def get_comment_ids_by_user_id(db: Session, user_id: int) -> list[int]:
    rows = db.query(Comment.id).filter(Comment.user_id == user_id).all()
    return [row[0] for row in rows]


def get_comment_ids_by_target_ids(
    db: Session,
    target_type: str,
    target_ids: list[int],
) -> list[int]:
    if not target_ids:
        return []
    rows = (
        db.query(Comment.id)
        .filter(
            Comment.target_type == target_type,
            Comment.target_id.in_(target_ids),
        )
        .all()
    )
    return [row[0] for row in rows]


def get_child_comment_ids_by_parent_ids(
    db: Session, parent_ids: list[int]
) -> list[int]:
    if not parent_ids:
        return []
    rows = db.query(Comment.id).filter(Comment.parent_id.in_(parent_ids)).all()
    return [row[0] for row in rows]


# ---------- 点赞相关 ----------


def get_user_comment_like(
    db: Session, comment_id: int, user_id: int
) -> UserCommentLike | None:
    return (
        db.query(UserCommentLike)
        .filter(
            UserCommentLike.comment_id == comment_id,
            UserCommentLike.user_id == user_id,
        )
        .first()
    )


def create_user_comment_like(db: Session, comment_id: int, user_id: int) -> UserCommentLike:
    db_like = UserCommentLike(comment_id=comment_id, user_id=user_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def delete_user_comment_like(db: Session, comment_id: int, user_id: int) -> int:
    result = (
        db.query(UserCommentLike)
        .filter(
            UserCommentLike.comment_id == comment_id,
            UserCommentLike.user_id == user_id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def delete_comment_likes_by_comment_ids(
    db: Session, comment_ids: list[int], auto_commit: bool = True
) -> int:
    if not comment_ids:
        return 0
    result = (
        db.query(UserCommentLike)
        .filter(UserCommentLike.comment_id.in_(comment_ids))
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def get_user_liked_comment_ids(
    db: Session,
    user_id: int,
    comment_ids: list[int],
) -> set[int]:
    if not comment_ids:
        return set()
    rows = (
        db.query(UserCommentLike.comment_id)
        .filter(
            UserCommentLike.user_id == user_id,
            UserCommentLike.comment_id.in_(comment_ids),
        )
        .all()
    )
    return {row[0] for row in rows}
