from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.schemas.blog_category import BlogCategoryCreate, BlogCategoryUpdate


def get_category_by_id(db: Session, category_id: int) -> BlogCategory | None:
    return db.query(BlogCategory).filter(BlogCategory.id == category_id).first()


def get_category_by_slug(db: Session, slug: str) -> BlogCategory | None:
    return db.query(BlogCategory).filter(BlogCategory.slug == slug).first()


def get_all_categories(db: Session) -> list[BlogCategory]:
    return db.query(BlogCategory).all()


def create_category(db: Session, category_in: BlogCategoryCreate) -> BlogCategory:
    db_category = BlogCategory(**category_in.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session, db_category: BlogCategory, category_in: BlogCategoryUpdate
) -> BlogCategory:
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> int:
    result = (
        db.query(BlogCategory)
        .filter(BlogCategory.id == category_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def count_posts_in_category(db: Session, category_id: int) -> int:
    return (
        db.query(func.count(BlogPost.id))
        .filter(
            BlogPost.category_id == category_id,
        )
        .scalar()
        or 0
    )
