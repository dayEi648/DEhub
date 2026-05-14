from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.user_blog_post_favorite import UserBlogPostFavorite
from app.models.user_zone_follow import UserZoneFollow
from app.models.user_post_favorite import UserPostFavorite
from app.models.blog_post import BlogPost
from app.models.forum_zone import ForumZone
from app.models.forum_post import ForumPost


# ---------- 博客文章收藏 ----------


def get_blog_post_favorite(
    db: Session, user_id: int, blog_post_id: int
) -> UserBlogPostFavorite | None:
    """
    查询用户对某篇博客文章的收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        blog_post_id: 博客文章ID
    Returns:
        UserBlogPostFavorite | None: 收藏记录或None
    """
    return (
        db.query(UserBlogPostFavorite)
        .filter(
            UserBlogPostFavorite.user_id == user_id,
            UserBlogPostFavorite.blog_post_id == blog_post_id,
        )
        .first()
    )


def create_blog_post_favorite(
    db: Session, user_id: int, blog_post_id: int
) -> UserBlogPostFavorite:
    """
    创建博客文章收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        blog_post_id: 博客文章ID
    Returns:
        UserBlogPostFavorite: 收藏记录对象
    """
    db_favorite = UserBlogPostFavorite(user_id=user_id, blog_post_id=blog_post_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


def delete_blog_post_favorite(
    db: Session, user_id: int, blog_post_id: int
) -> int:
    """
    删除博客文章收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        blog_post_id: 博客文章ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserBlogPostFavorite)
        .filter(
            UserBlogPostFavorite.user_id == user_id,
            UserBlogPostFavorite.blog_post_id == blog_post_id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def get_user_blog_post_favorites(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> tuple[list[BlogPost], int]:
    """
    获取用户的博客文章收藏列表（自动 join 分类信息，按收藏时间倒序）
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过数量
        limit: 限制数量
        status: 状态筛选
    Returns:
        tuple[list[BlogPost], int]: 文章列表与总条数
    """
    query = (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category))
        .join(
            UserBlogPostFavorite,
            BlogPost.id == UserBlogPostFavorite.blog_post_id,
        )
        .filter(UserBlogPostFavorite.user_id == user_id)
        .filter(BlogPost.is_deleted == False)
    )
    if status:
        query = query.filter(BlogPost.status == status)
    query = query.order_by(UserBlogPostFavorite.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


# ---------- 分区关注 ----------


def get_zone_follow(
    db: Session, user_id: int, zone_id: int
) -> UserZoneFollow | None:
    """
    查询用户对某分区的关注记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        zone_id: 分区ID
    Returns:
        UserZoneFollow | None: 关注记录或None
    """
    return (
        db.query(UserZoneFollow)
        .filter(
            UserZoneFollow.user_id == user_id,
            UserZoneFollow.zone_id == zone_id,
        )
        .first()
    )


def create_zone_follow(
    db: Session, user_id: int, zone_id: int
) -> UserZoneFollow:
    """
    创建分区关注记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        zone_id: 分区ID
    Returns:
        UserZoneFollow: 关注记录对象
    """
    db_follow = UserZoneFollow(user_id=user_id, zone_id=zone_id)
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    return db_follow


def delete_zone_follow(
    db: Session, user_id: int, zone_id: int
) -> int:
    """
    删除分区关注记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        zone_id: 分区ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserZoneFollow)
        .filter(
            UserZoneFollow.user_id == user_id,
            UserZoneFollow.zone_id == zone_id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def get_user_zone_follows(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[ForumZone], int]:
    """
    获取用户的分区关注列表（自动 join 区主信息，按关注时间倒序）
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过数量
        limit: 限制数量
    Returns:
        tuple[list[ForumZone], int]: 分区列表与总条数
    """
    query = (
        db.query(ForumZone)
        .options(joinedload(ForumZone.manager))
        .join(UserZoneFollow, ForumZone.id == UserZoneFollow.zone_id)
        .filter(UserZoneFollow.user_id == user_id)
        .order_by(UserZoneFollow.created_at.desc())
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


# ---------- 论坛帖子收藏 ----------


def get_post_favorite(
    db: Session, user_id: int, post_id: int
) -> UserPostFavorite | None:
    """
    查询用户对某帖子的收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        post_id: 帖子ID
    Returns:
        UserPostFavorite | None: 收藏记录或None
    """
    return (
        db.query(UserPostFavorite)
        .filter(
            UserPostFavorite.user_id == user_id,
            UserPostFavorite.post_id == post_id,
        )
        .first()
    )


def create_post_favorite(
    db: Session, user_id: int, post_id: int
) -> UserPostFavorite:
    """
    创建帖子收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        post_id: 帖子ID
    Returns:
        UserPostFavorite: 收藏记录对象
    """
    db_favorite = UserPostFavorite(user_id=user_id, post_id=post_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


def delete_post_favorite(
    db: Session, user_id: int, post_id: int
) -> int:
    """
    删除帖子收藏记录
    Args:
        db: 数据库会话
        user_id: 用户ID
        post_id: 帖子ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserPostFavorite)
        .filter(
            UserPostFavorite.user_id == user_id,
            UserPostFavorite.post_id == post_id,
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def get_user_post_favorites(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[ForumPost], int]:
    """
    获取用户的论坛帖子收藏列表（自动 join 用户和分区信息，按收藏时间倒序）
    Args:
        db: 数据库会话
        user_id: 用户ID
        skip: 跳过数量
        limit: 限制数量
    Returns:
        tuple[list[ForumPost], int]: 帖子列表与总条数
    """
    query = (
        db.query(ForumPost)
        .options(joinedload(ForumPost.user), joinedload(ForumPost.zone))
        .join(UserPostFavorite, ForumPost.id == UserPostFavorite.post_id)
        .filter(UserPostFavorite.user_id == user_id)
        .order_by(UserPostFavorite.created_at.desc())
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total
