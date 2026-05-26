from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload
from app.models.forum_reply import ForumReply
from app.models.user_forum_reply_like import UserForumReplyLike
from app.schemas.forum_reply import ForumReplyCreate


def get_reply_by_id(db: Session, reply_id: int) -> ForumReply | None:
    """
    根据回复ID获取回复（自动 join 用户信息）
    Args:
        db: 数据库会话
        reply_id: 回复ID
    Returns:
        ForumReply | None: 回复对象或None
    """
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
    """
    分页查询某帖子下的回复列表（按时间倒序，自动 join 用户信息）
    Args:
        db: 数据库会话
        post_id: 帖子ID
        skip: 跳过数量
        limit: 限制数量
    Returns:
        tuple[list[ForumReply], int]: 回复列表与总条数
    """
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
    """
    创建回复
    Args:
        db: 数据库会话
        reply_in: 回复创建请求
        user_id: 当前登录用户ID
    Returns:
        ForumReply: 回复对象
    """
    db_reply = ForumReply(**reply_in.model_dump(), user_id=user_id)
    db.add(db_reply)
    if auto_commit:
        db.commit()
    else:
        db.flush()
    db.refresh(db_reply)
    return db_reply


def get_all_replies_by_post_id(db: Session, post_id: int) -> list[ForumReply]:
    """
    查询某帖子下的全部回复（用于删除级联清理）
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        list[ForumReply]: 回复列表
    """
    return db.query(ForumReply).filter(ForumReply.post_id == post_id).all()


def delete_reply(db: Session, reply_id: int, auto_commit: bool = True) -> int:
    """
    删除回复（物理删除）
    Args:
        db: 数据库会话
        reply_id: 回复ID
    Returns:
        int: 删除行数
    """
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
    """
    按帖子 ID 批量删除回复
    Args:
        db: 数据库会话
        post_ids: 帖子 ID 列表
    Returns:
        int: 删除行数
    """
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
    """
    按用户 ID 批量删除回复
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        int: 删除行数
    """
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
    """
    查询用户对某条回复的点赞记录
    Args:
        db: 数据库会话
        reply_id: 回复ID
        user_id: 用户ID
    Returns:
        UserForumReplyLike | None: 点赞记录或None
    """
    return (
        db.query(UserForumReplyLike)
        .filter(
            UserForumReplyLike.reply_id == reply_id,
            UserForumReplyLike.user_id == user_id,
        )
        .first()
    )


def create_user_forum_reply_like(
    db: Session, reply_id: int, user_id: int
) -> UserForumReplyLike:
    """
    创建回复点赞记录
    Args:
        db: 数据库会话
        reply_id: 回复ID
        user_id: 用户ID
    Returns:
        UserForumReplyLike: 点赞记录对象
    """
    db_like = UserForumReplyLike(reply_id=reply_id, user_id=user_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def delete_user_forum_reply_like(db: Session, reply_id: int, user_id: int) -> int:
    """
    删除回复点赞记录
    Args:
        db: 数据库会话
        reply_id: 回复ID
        user_id: 用户ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserForumReplyLike)
        .filter(
            UserForumReplyLike.reply_id == reply_id,
            UserForumReplyLike.user_id == user_id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def get_user_liked_reply_ids(
    db: Session,
    user_id: int,
    reply_ids: list[int],
) -> set[int]:
    """
    批量查询用户已点赞的回复 ID。
    Args:
        db: 数据库会话
        user_id: 用户ID
        reply_ids: 回复 ID 列表
    Returns:
        set[int]: 已点赞回复 ID 集合
    """
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
    """
    按回复 ID 列表批量删除点赞记录
    Args:
        db: 数据库会话
        reply_ids: 回复 ID 列表
    Returns:
        int: 删除行数
    """
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
    """
    按用户 ID 批量删除回复点赞记录
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserForumReplyLike)
        .filter(UserForumReplyLike.user_id == user_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result
