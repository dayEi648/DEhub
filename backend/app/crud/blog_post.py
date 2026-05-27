from sqlalchemy.orm import Session, joinedload
from app.models.blog_post import BlogPost
from app.schemas.blog_post import BlogPostCreate, BlogPostUpdate

def get_blog_post_by_id(db: Session, post_id: int) -> BlogPost | None:
    return (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category), joinedload(BlogPost.user))
        .filter(
            BlogPost.id == post_id
        )
        .first()
    )

def get_blog_post_by_slug(db: Session, slug: str) -> BlogPost | None:
    return (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category), joinedload(BlogPost.user))
        .filter(
            BlogPost.slug == slug
        )
        .first()
    )

def get_blog_posts(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    category_id: int | None = None,
    tag: str | None = None,
    q: str | None = None
) -> list[BlogPost]:
    query = db.query(BlogPost).options(joinedload(BlogPost.category), joinedload(BlogPost.user))

    if status:
        query = query.filter(BlogPost.status == status)
    if category_id is not None:
        query = query.filter(BlogPost.category_id == category_id)
    if tag:
        query = query.filter(BlogPost.tags.contains([tag]))
    if q:
        query = query.filter(BlogPost.title.ilike(f"%{q}%"))

    return query.order_by(BlogPost.created_at.desc()).offset(skip).limit(limit).all()


def get_blog_posts_count(
    db: Session,
    status: str | None = None,
    category_id: int | None = None,
    tag: str | None = None,
    q: str | None = None,
) -> int:
    query = db.query(BlogPost)

    if status:
        query = query.filter(BlogPost.status == status)
    if category_id is not None:
        query = query.filter(BlogPost.category_id == category_id)
    if tag:
        query = query.filter(BlogPost.tags.contains([tag]))
    if q:
        query = query.filter(BlogPost.title.ilike(f"%{q}%"))

    return query.count()


def create_blog_post(
    db: Session,
    post_in: BlogPostCreate,
    user_id: int,
    cover_image_url: str | None = None,
) -> BlogPost:
    post_data = post_in.model_dump()
    if cover_image_url is not None:
        post_data["cover_image_url"] = cover_image_url
    db_post = BlogPost(**post_data, user_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_blog_post(db: Session, db_post: BlogPost, post_in: BlogPostUpdate) -> BlogPost:
    update_data = post_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def hard_delete_blog_post(db: Session, post_id: int) -> int:
    result = db.query(BlogPost).filter(
        BlogPost.id == post_id
    ).delete(synchronize_session=False)
    db.commit()
    return result

def increment_view_count(db: Session, post_id: int) -> int:
    result = db.query(BlogPost).filter(
        BlogPost.id == post_id
    ).update(
        {"view_count": BlogPost.view_count + 1},
        synchronize_session=False
    )
    db.commit()
    return result
