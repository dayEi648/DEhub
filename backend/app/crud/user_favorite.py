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
    db_favorite = UserBlogPostFavorite(user_id=user_id, blog_post_id=blog_post_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


def delete_blog_post_favorite(
    db: Session, user_id: int, blog_post_id: int
) -> int:
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
    query = (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category))
        .join(
            UserBlogPostFavorite,
            BlogPost.id == UserBlogPostFavorite.blog_post_id,
        )
        .filter(UserBlogPostFavorite.user_id == user_id)
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
    db_follow = UserZoneFollow(user_id=user_id, zone_id=zone_id)
    db.add(db_follow)
    db.commit()
    db.refresh(db_follow)
    return db_follow


def delete_zone_follow(
    db: Session, user_id: int, zone_id: int
) -> int:
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
    db_favorite = UserPostFavorite(user_id=user_id, post_id=post_id)
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite


def delete_post_favorite(
    db: Session, user_id: int, post_id: int
) -> int:
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


# ---------- 用户级联清理 ----------


def delete_all_favorites_by_user_id(
    db: Session, user_id: int, auto_commit: bool = True
) -> dict[str, int]:
    blog_fav = (
        db.query(UserBlogPostFavorite)
        .filter(UserBlogPostFavorite.user_id == user_id)
        .delete(synchronize_session=False)
    )
    zone_follow = (
        db.query(UserZoneFollow)
        .filter(UserZoneFollow.user_id == user_id)
        .delete(synchronize_session=False)
    )
    post_fav = (
        db.query(UserPostFavorite)
        .filter(UserPostFavorite.user_id == user_id)
        .delete(synchronize_session=False)
    )
    if auto_commit:
        db.commit()
    return {
        "blog_post_favorites": blog_fav,
        "zone_follows": zone_follow,
        "post_favorites": post_fav,
    }
