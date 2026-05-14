from sqlalchemy.orm import Session, joinedload
from app.models.blog_post import BlogPost
from app.schemas.blog_post import BlogPostCreate, BlogPostUpdate

def get_blog_post_by_id(db: Session, post_id: int) -> BlogPost | None:
    """
    根据文章ID获取文章（排除已删除，自动 join 分类信息）
    Args:
        db: 数据库会话
        post_id: 文章ID
    Returns:
        BlogPost | None: 文章对象或None
    """
    return (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category))
        .filter(
            BlogPost.id == post_id,
            BlogPost.is_deleted == False
        )
        .first()
    )

def get_blog_post_by_slug(db: Session, slug: str) -> BlogPost | None:
    """
    根据文章 slug 获取文章（排除已删除，自动 join 分类信息）
    Args:
        db: 数据库会话
        slug: 文章 slug
    Returns:
        BlogPost | None: 文章对象或None
    """
    return (
        db.query(BlogPost)
        .options(joinedload(BlogPost.category))
        .filter(
            BlogPost.slug == slug,
            BlogPost.is_deleted == False
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
    """
    获取文章列表（排除已删除，支持过滤与分页，自动 join 分类信息）
    Args:
        db: 数据库会话
        skip: 跳过数量
        limit: 限制数量
        status: 状态筛选
        category_id: 分类ID筛选
        tag: 标签筛选（精确匹配单个标签）
    Returns:
        list[BlogPost]: 文章列表
    """
    query = db.query(BlogPost).options(joinedload(BlogPost.category)).filter(BlogPost.is_deleted == False)

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
    """
    获取文章列表的总数量（与 get_blog_posts 使用相同的过滤条件）。

    Args:
        db: 数据库会话
        status: 状态筛选
        category_id: 分类ID筛选
        tag: 标签筛选
        q: 标题关键词搜索

    Returns:
        int: 符合条件的文章总数
    """
    query = db.query(BlogPost).filter(BlogPost.is_deleted == False)

    if status:
        query = query.filter(BlogPost.status == status)
    if category_id is not None:
        query = query.filter(BlogPost.category_id == category_id)
    if tag:
        query = query.filter(BlogPost.tags.contains([tag]))
    if q:
        query = query.filter(BlogPost.title.ilike(f"%{q}%"))

    return query.count()


def create_blog_post(db: Session, post_in: BlogPostCreate) -> BlogPost:
    """
    创建文章
    Args:
        db: 数据库会话
        post_in: 文章创建请求
    Returns:
        BlogPost: 文章对象
    """
    db_post = BlogPost(**post_in.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def update_blog_post(db: Session, db_post: BlogPost, post_in: BlogPostUpdate) -> BlogPost:
    """
    更新文章
    Args:
        db: 数据库会话
        db_post: 文章对象
        post_in: 文章更新请求
    Returns:
        BlogPost: 文章对象
    """
    update_data = post_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_post, field, value)
    db.commit()
    db.refresh(db_post)
    return db_post

def soft_delete_blog_post(db: Session, post_id: int) -> int:
    """
    软删除文章
    Args:
        db: 数据库会话
        post_id: 文章ID
    Returns:
        int: 更新行数
    """
    result = db.query(BlogPost).filter(
        BlogPost.id == post_id,
        BlogPost.is_deleted == False
    ).update({"is_deleted": True}, synchronize_session=False)
    db.commit()
    return result

def hard_delete_blog_post(db: Session, post_id: int) -> int:
    """
    硬删除文章
    Args:
        db: 数据库会话
        post_id: 文章ID
    Returns:
        int: 删除行数
    """
    result = db.query(BlogPost).filter(
        BlogPost.id == post_id
    ).delete(synchronize_session=False)
    db.commit()
    return result

def cleanup_deleted_posts(db: Session) -> int:
    """
    一键清理所有已逻辑删除的博客文章
    Args:
        db: 数据库会话
    Returns:
        int: 删除行数
    """
    result = db.query(BlogPost).filter(BlogPost.is_deleted == True).delete(synchronize_session=False)
    db.commit()
    return result

def increment_view_count(db: Session, post_id: int) -> int:
    """
    增加文章浏览量
    Args:
        db: 数据库会话
        post_id: 文章ID
    Returns:
        int: 更新行数
    """
    result = db.query(BlogPost).filter(
        BlogPost.id == post_id
    ).update(
        {"view_count": BlogPost.view_count + 1},
        synchronize_session=False
    )
    db.commit()
    return result
