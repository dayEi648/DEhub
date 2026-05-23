from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload
from app.models.forum_post import ForumPost
from app.schemas.forum_post import ForumPostCreate, ForumPostUpdate


def get_post_by_id(db: Session, post_id: int) -> ForumPost | None:
    """
    根据帖子ID获取帖子（自动 join 用户信息）
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        ForumPost | None: 帖子对象或None
    """
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
    """
    获取帖子列表（支持分区过滤、排序与分页，自动 join 用户信息）
    Args:
        db: 数据库会话
        zone_id: 分区ID筛选
        sort_by: 排序方式，"created" 按发布时间倒序，"view" 按浏览量倒序
        skip: 跳过数量
        limit: 限制数量
    Returns:
        tuple[list[ForumPost], int]: 帖子列表与总条数
    """
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
    """
    创建帖子
    Args:
        db: 数据库会话
        post_in: 帖子创建请求
        user_id: 当前登录用户ID
    Returns:
        ForumPost: 帖子对象
    """
    db_post = ForumPost(**post_in.model_dump(), user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def update_post(
    db: Session, db_post: ForumPost, post_in: ForumPostUpdate
) -> ForumPost:
    """
    更新帖子
    Args:
        db: 数据库会话
        db_post: 帖子对象
        post_in: 帖子更新请求
    Returns:
        ForumPost: 帖子对象
    """
    update_data = post_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: int, auto_commit: bool = True) -> int:
    """
    删除帖子（物理删除）
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(ForumPost)
        .filter(ForumPost.id == post_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return result


def get_post_ids_by_user_id(db: Session, user_id: int) -> list[int]:
    """
    获取某用户发表的所有帖子 ID
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        list[int]: 帖子 ID 列表
    """
    rows = db.query(ForumPost.id).filter(ForumPost.user_id == user_id).all()
    return [row[0] for row in rows]


def increment_post_view_count(db: Session, post_id: int) -> int:
    """
    增加帖子浏览量
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        int: 更新行数
    """
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"view_count": ForumPost.view_count + 1},
        synchronize_session=False,
    )
    db.commit()
    return result


def increment_reply_count(db: Session, post_id: int) -> int:
    """
    增加帖子回复数
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        int: 更新行数
    """
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"reply_count": ForumPost.reply_count + 1},
        synchronize_session=False,
    )
    db.commit()
    return result


def decrement_reply_count(db: Session, post_id: int) -> int:
    """
    减少帖子回复数（SQL 层面兜底下限为 0）
    Args:
        db: 数据库会话
        post_id: 帖子ID
    Returns:
        int: 更新行数
    """
    result = db.query(ForumPost).filter(ForumPost.id == post_id).update(
        {"reply_count": func.greatest(ForumPost.reply_count - 1, 0)},
        synchronize_session=False,
    )
    db.commit()
    return result
