from pgvector.sqlalchemy import Vector
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.models.user_memory_embedding import UserMemoryEmbedding


def create_memory_embedding(
    db: Session,
    user_id: int,
    conversation_id: int,
    memory_type: str,
    content_text: str,
    embedding: list[float],
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
    db.commit()
    db.refresh(record)
    return record


def delete_memories_by_conversation(db: Session, conversation_id: int) -> int:
    """按对话 ID 删除所有相关记忆。"""
    result = (
        db.query(UserMemoryEmbedding)
        .filter(UserMemoryEmbedding.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def search_user_memories(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    top_k: int = 3,
) -> list[tuple[UserMemoryEmbedding, float]]:
    """
    基于余弦距离检索某用户的相关记忆。

    使用 pgvector 的 `<=>`（余弦距离）算子，距离越小越相似。
    """
    stmt = text(
        """
        SELECT id, user_id, conversation_id, memory_type, content_text, embedding, created_at,
               embedding <=> :embedding AS distance
        FROM user_memory_embeddings
        WHERE user_id = :user_id
        ORDER BY embedding <=> :embedding
        LIMIT :top_k
        """
    ).bindparams(
        bindparam("embedding", query_embedding, type_=Vector(1024)),
        user_id=user_id,
        top_k=top_k,
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
