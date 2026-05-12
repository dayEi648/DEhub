from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.schemas.blog_category import BlogCategoryCreate, BlogCategoryUpdate


def get_category_by_id(db: Session, category_id: int) -> BlogCategory | None:
    """
    根据分类ID获取分类
    Args:
        db: 数据库会话
        category_id: 分类ID
    Returns:
        BlogCategory | None: 分类对象或None
    """
    return db.query(BlogCategory).filter(BlogCategory.id == category_id).first()


def get_category_by_slug(db: Session, slug: str) -> BlogCategory | None:
    """
    根据分类 slug 获取分类
    Args:
        db: 数据库会话
        slug: 分类 slug
    Returns:
        BlogCategory | None: 分类对象或None
    """
    return db.query(BlogCategory).filter(BlogCategory.slug == slug).first()


def get_all_categories(db: Session) -> list[BlogCategory]:
    """
    获取所有分类
    Args:
        db: 数据库会话
    Returns:
        list[BlogCategory]: 分类列表
    """
    return db.query(BlogCategory).all()


def create_category(db: Session, category_in: BlogCategoryCreate) -> BlogCategory:
    """
    创建分类
    Args:
        db: 数据库会话
        category_in: 分类创建请求
    Returns:
        BlogCategory: 分类对象
    """
    db_category = BlogCategory(**category_in.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session, db_category: BlogCategory, category_in: BlogCategoryUpdate
) -> BlogCategory:
    """
    更新分类
    Args:
        db: 数据库会话
        db_category: 分类对象
        category_in: 分类更新请求
    Returns:
        BlogCategory: 分类对象
    """
    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> int:
    """
    删除分类
    Args:
        db: 数据库会话
        category_id: 分类ID
    Returns:
        int: 删除行数
    """
    result = (
        db.query(BlogCategory)
        .filter(BlogCategory.id == category_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def count_posts_in_category(db: Session, category_id: int) -> int:
    """
    统计某分类下的未删除文章数量
    Args:
        db: 数据库会话
        category_id: 分类ID
    Returns:
        int: 文章数量
    """
    return (
        db.query(func.count(BlogPost.id))
        .filter(
            BlogPost.category_id == category_id,
            BlogPost.is_deleted == False,
        )
        .scalar()
        or 0
    )
