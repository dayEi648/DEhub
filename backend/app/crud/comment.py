from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.comment import Comment
from app.models.user_comment_like import UserCommentLike
from app.schemas.comment import CommentCreate


def get_comment_by_id(db: Session, comment_id: int) -> Comment | None:
    """
    根据评论ID获取评论
    Args:
        db: 数据库会话
        comment_id: 评论ID
    Returns:
        Comment | None: 评论对象或None
    """
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
    sort_by: str = "time",
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Comment], int]:
    """
    分页查询评论列表（自动 join 用户信息）
    Args:
        db: 数据库会话
        target_type: 目标类型
        target_id: 目标ID
        parent_id: 父评论ID，None 表示查询一级评论
        sort_by: 排序方式，"time" 按时间倒序，"hot" 按热度（点赞数）倒序
        skip: 跳过数量
        limit: 限制数量
    Returns:
        tuple[list[Comment], int]: 评论列表与总条数
    """
    query = db.query(Comment).filter(
        Comment.target_type == target_type,
        Comment.target_id == target_id,
    )

    if parent_id is not None:
        query = query.filter(Comment.parent_id == parent_id)
    # parent_id 为 None 时，不额外过滤 parent_id，返回该目标下所有层级的评论

    if sort_by == "hot":
        query = query.order_by(desc(Comment.likecount), desc(Comment.created_at))
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


def create_comment(db: Session, comment_in: CommentCreate, user_id: int) -> Comment:
    """
    创建评论
    Args:
        db: 数据库会话
        comment_in: 评论创建请求
        user_id: 当前登录用户ID
    Returns:
        Comment: 评论对象
    """
    db_comment = Comment(
        target_type=comment_in.target_type,
        target_id=comment_in.target_id,
        parent_id=comment_in.parent_id,
        user_id=user_id,
        content=comment_in.content,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


def delete_comment(db: Session, comment_id: int) -> int:
    """
    物理删除评论
    Args:
        db: 数据库会话
        comment_id: 评论ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(Comment)
        .filter(Comment.id == comment_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def get_comment_ids_by_user_id(db: Session, user_id: int) -> list[int]:
    """
    获取某用户发表的所有评论 ID
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        list[int]: 评论 ID 列表
    """
    rows = db.query(Comment.id).filter(Comment.user_id == user_id).all()
    return [row[0] for row in rows]


def get_child_comment_ids_by_parent_ids(
    db: Session, parent_ids: list[int]
) -> list[int]:
    """
    获取 parent_id 在指定列表中的所有子评论 ID
    Args:
        db: 数据库会话
        parent_ids: 父评论 ID 列表
    Returns:
        list[int]: 子评论 ID 列表
    """
    if not parent_ids:
        return []
    rows = db.query(Comment.id).filter(Comment.parent_id.in_(parent_ids)).all()
    return [row[0] for row in rows]


def delete_comments_by_ids(db: Session, comment_ids: list[int]) -> int:
    """
    按评论 ID 列表批量删除评论
    Args:
        db: 数据库会话
        comment_ids: 评论 ID 列表
    Returns:
        int: 删除行数
    """
    if not comment_ids:
        return 0
    result = (
        db.query(Comment)
        .filter(Comment.id.in_(comment_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


# ---------- 点赞相关 ----------


def get_user_comment_like(
    db: Session, comment_id: int, user_id: int
) -> UserCommentLike | None:
    """
    查询用户对某条评论的点赞记录
    Args:
        db: 数据库会话
        comment_id: 评论ID
        user_id: 用户ID
    Returns:
        UserCommentLike | None: 点赞记录或None
    """
    return (
        db.query(UserCommentLike)
        .filter(
            UserCommentLike.comment_id == comment_id,
            UserCommentLike.user_id == user_id,
        )
        .first()
    )


def create_user_comment_like(db: Session, comment_id: int, user_id: int) -> UserCommentLike:
    """
    创建点赞记录
    Args:
        db: 数据库会话
        comment_id: 评论ID
        user_id: 用户ID
    Returns:
        UserCommentLike: 点赞记录对象
    """
    db_like = UserCommentLike(comment_id=comment_id, user_id=user_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return db_like


def delete_user_comment_like(db: Session, comment_id: int, user_id: int) -> int:
    """
    删除点赞记录
    Args:
        db: 数据库会话
        comment_id: 评论ID
        user_id: 用户ID
    Returns:
        int: 删除行数
    """
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
    db: Session, comment_ids: list[int]
) -> int:
    """
    按评论 ID 列表批量删除点赞记录
    Args:
        db: 数据库会话
        comment_ids: 评论 ID 列表
    Returns:
        int: 删除行数
    """
    if not comment_ids:
        return 0
    result = (
        db.query(UserCommentLike)
        .filter(UserCommentLike.comment_id.in_(comment_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    return result
