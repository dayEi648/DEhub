from sqlalchemy import desc
from sqlalchemy.orm import Session
from app.models.forum_reply import ForumReply
from app.schemas.forum_reply import ForumReplyCreate


def get_reply_by_id(db: Session, reply_id: int) -> ForumReply | None:
    """
    根据回复ID获取回复
    Args:
        db: 数据库会话
        reply_id: 回复ID
    Returns:
        ForumReply | None: 回复对象或None
    """
    return db.query(ForumReply).filter(ForumReply.id == reply_id).first()


def get_replies_by_post_id(
    db: Session,
    post_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[ForumReply], int]:
    """
    分页查询某帖子下的回复列表（按时间倒序）
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
        query.order_by(desc(ForumReply.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def create_reply(db: Session, reply_in: ForumReplyCreate, user_id: int) -> ForumReply:
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
    db.commit()
    db.refresh(db_reply)
    return db_reply


def delete_reply(db: Session, reply_id: int) -> int:
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
    db.commit()
    return result


def increment_like_count(db: Session, reply_id: int) -> int:
    """
    增加回复点赞数
    Args:
        db: 数据库会话
        reply_id: 回复ID
    Returns:
        int: 更新行数
    """
    result = db.query(ForumReply).filter(ForumReply.id == reply_id).update(
        {"likecount": ForumReply.likecount + 1},
        synchronize_session=False,
    )
    db.commit()
    return result
