from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, Integer, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.blog_post_embedding import BlogPostEmbedding


def get_embedding_by_post_id(db: Session, post_id: int) -> BlogPostEmbedding | None:
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
    category_id: int | None = None,
) -> list[tuple[BlogPostEmbedding, float]]:
    if category_id is not None:
        stmt = text(
            """
            SELECT e.id, e.post_id, e.embedding, e.content_hash, e.created_at, e.updated_at,
                   e.embedding <=> :embedding AS distance
            FROM blog_post_embeddings e
            JOIN blog_posts p ON e.post_id = p.id
            WHERE p.category_id = :category_id
            ORDER BY e.embedding <=> :embedding
            LIMIT :top_k
            """
        ).bindparams(
            bindparam("embedding", query_embedding, type_=Vector(settings.EMBEDDING_DIMENSION_EFFECTIVE)),
            bindparam("category_id", category_id, type_=Integer),
            top_k=top_k,
        )
    else:
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
