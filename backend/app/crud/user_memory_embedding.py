from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user_memory_embedding import UserMemoryEmbedding


def create_memory_embedding(
    db: Session,
    user_id: int,
    conversation_id: int,
    memory_type: str,
    content_text: str,
    embedding: list[float],
    commit: bool = True,
) -> UserMemoryEmbedding:
    """插入单条用户记忆向量。"""
    record = UserMemoryEmbedding(
        user_id=user_id,
        conversation_id=conversation_id,
        memory_type=memory_type,
        content_text=content_text,
        embedding=embedding,
    )
    db.add(record)
    if commit:
        db.commit()
        db.refresh(record)
    return record


def delete_memories_by_conversation(
    db: Session, conversation_id: int, commit: bool = True
) -> int:
    """按对话 ID 删除所有相关记忆。"""
    result = (
        db.query(UserMemoryEmbedding)
        .filter(UserMemoryEmbedding.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )
    if commit:
        db.commit()
    return result


def search_user_memories(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    top_k: int = 3,
    max_distance: float | None = None,
) -> list[tuple[UserMemoryEmbedding, float]]:
    """
    基于余弦距离检索某用户的相关记忆。

    使用 pgvector 的 `<=>`（余弦距离）算子，距离越小越相似。
    当传入 max_distance 时，只返回距离小于该值的记录。
    余弦相似度 = 1 - 余弦距离，因此相似度 > 0.6 等价于 max_distance = 0.4。

    只检索 created_at 在 1 年以内的记录，避免过期的画像干扰当前对话。
    """
    # 动态构建 WHERE 子句
    distance_where = ""
    bind_kwargs: dict = {
        "user_id": user_id,
        "top_k": top_k,
        "retention_days": settings.MEMORY_RETENTION_DAYS,
    }
    if max_distance is not None:
        distance_where = "AND embedding <=> :embedding < :max_distance"
        bind_kwargs["max_distance"] = max_distance

    stmt = text(
        f"""
        SELECT id, user_id, conversation_id, memory_type, content_text, embedding, created_at,
               embedding <=> :embedding AS distance
        FROM user_memory_embeddings
        WHERE user_id = :user_id
          AND created_at >= NOW() - INTERVAL '1 day' * :retention_days
        {distance_where}
        ORDER BY embedding <=> :embedding
        LIMIT :top_k
        """
    ).bindparams(
        bindparam(
            "embedding",
            query_embedding,
            type_=Vector(settings.EMBEDDING_DIMENSION_EFFECTIVE),
        ),
        **bind_kwargs,
    )

    rows = db.execute(stmt).all()

    results: list[tuple[UserMemoryEmbedding, float]] = []
    for row in rows:
        record = UserMemoryEmbedding(
            id=row.id,
            user_id=row.user_id,
            conversation_id=row.conversation_id,
            memory_type=row.memory_type,
            content_text=row.content_text,
            embedding=row.embedding,
            created_at=row.created_at,
        )
        results.append((record, float(row.distance)))

    return results
