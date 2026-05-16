from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.blog_post_embedding import BlogPostEmbedding


def get_embedding_by_post_id(db: Session, post_id: int) -> BlogPostEmbedding | None:
    """
    根据文章 ID 获取向量记录。

    Args:
        db: 数据库会话
        post_id: 文章 ID

    Returns:
        BlogPostEmbedding | None
    """
    return (
        db.query(BlogPostEmbedding)
        .filter(BlogPostEmbedding.post_id == post_id)
        .first()
    )


def upsert_embedding(
    db: Session,
    post_id: int,
    embedding: list[float],
    content_hash: str | None = None,
) -> BlogPostEmbedding:
    """
    插入或更新文章的向量记录。

    若 post_id 已存在则更新 embedding 和 content_hash，
    否则新建记录。

    Args:
        db: 数据库会话
        post_id: 文章 ID
        embedding: 向量（维度由 EMBEDDING_DIMENSION 配置决定，默认 1024）
        content_hash: 内容指纹，用于跳过无变化的重复嵌入

    Returns:
        BlogPostEmbedding: 更新或新建的记录
    """
    existing = get_embedding_by_post_id(db, post_id)
    if existing:
        existing.embedding = embedding
        existing.content_hash = content_hash
        db.commit()
        db.refresh(existing)
        return existing

    db_embedding = BlogPostEmbedding(
        post_id=post_id,
        embedding=embedding,
        content_hash=content_hash,
    )
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


def delete_embedding_by_post_id(db: Session, post_id: int) -> bool:
    """
    根据文章 ID 删除向量记录。

    Args:
        db: 数据库会话
        post_id: 文章 ID

    Returns:
        bool: 是否成功删除（记录存在且被删除）
    """
    result = (
        db.query(BlogPostEmbedding)
        .filter(BlogPostEmbedding.post_id == post_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0


def search_similar(
    db: Session,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[tuple[BlogPostEmbedding, float]]:
    """
    基于余弦距离检索最相似的博客文章向量。

    使用 pgvector 的 `<=>`（余弦距离）算子，距离越小越相似。
    返回结果按距离升序排列。

    Args:
        db: 数据库会话
        query_embedding: 查询向量
        top_k: 返回结果数量上限

    Returns:
        list[tuple[BlogPostEmbedding, float]]: (向量记录, 距离) 列表
    """
    stmt = text(
        """
        SELECT id, post_id, embedding, content_hash, created_at, updated_at,
               embedding <=> :embedding AS distance
        FROM blog_post_embeddings
        ORDER BY embedding <=> :embedding
        LIMIT :top_k
        """
    ).bindparams(
        bindparam("embedding", query_embedding, type_=Vector(settings.EMBEDDING_DIMENSION_EFFECTIVE)),
        top_k=top_k,
    )

    rows = db.execute(stmt).all()

    results: list[tuple[BlogPostEmbedding, float]] = []
    for row in rows:
        embedding = BlogPostEmbedding(
            id=row.id,
            post_id=row.post_id,
            embedding=row.embedding,
            content_hash=row.content_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        results.append((embedding, float(row.distance)))

    return results
