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
    """
    插入单条用户记忆向量。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        conversation_id: 对话 ID
        memory_type: 'turn' 或 'summary'
        content_text: 原始文本内容
        embedding: 1024 维向量

    Returns:
        UserMemoryEmbedding: 新建的记录
    """
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
    """
    按对话 ID 删除所有相关记忆。

    Args:
        db: 数据库会话
        conversation_id: 对话 ID

    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserMemoryEmbedding)
        .filter(UserMemoryEmbedding.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def delete_summary_by_conversation(db: Session, conversation_id: int) -> int:
    """
    删除指定对话的 summary 类型记忆（用于更新摘要时先清旧）。

    Args:
        db: 数据库会话
        conversation_id: 对话 ID

    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserMemoryEmbedding)
        .filter(
            UserMemoryEmbedding.conversation_id == conversation_id,
            UserMemoryEmbedding.memory_type == "summary",
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result


def search_user_memories(
    db: Session,
    user_id: int,
    query_embedding: list[float],
    since: str,
    top_k: int = 3,
    exclude_conversation_id: int | None = None,
) -> list[tuple[UserMemoryEmbedding, float]]:
    """
    基于余弦距离检索某用户在指定时间范围内的相关记忆。

    使用 pgvector 的 `<=>`（余弦距离）算子，距离越小越相似。
    必须同时过滤 user_id 和 created_at 下限，确保隐私与 retention。
    可选排除指定对话 ID，避免检索到当前对话自身的记忆（自我污染）。

    Args:
        db: 数据库会话
        user_id: 用户 ID
        query_embedding: 查询向量
        since: 时间下限字符串，如 '2024-01-01 00:00:00+00:00'
        top_k: 返回结果数量上限
        exclude_conversation_id: 需要排除的对话 ID（通常为当前对话）

    Returns:
        list[tuple[UserMemoryEmbedding, float]]: (记忆记录, 距离) 列表
    """
    exclude_clause = ""
    params = {
        "embedding": query_embedding,
        "user_id": user_id,
        "since": since,
        "top_k": top_k,
    }
    if exclude_conversation_id is not None:
        exclude_clause = "AND conversation_id != :exclude_conversation_id"
        params["exclude_conversation_id"] = exclude_conversation_id

    stmt = text(
        f"""
        SELECT id, user_id, conversation_id, memory_type, content_text, embedding, created_at,
               embedding <=> :embedding AS distance
        FROM user_memory_embeddings
        WHERE user_id = :user_id
          AND created_at > :since
          {exclude_clause}
        ORDER BY embedding <=> :embedding
        LIMIT :top_k
        """
    ).bindparams(
        bindparam("embedding", query_embedding, type_=Vector(1024)),
        **{k: v for k, v in params.items() if k != "embedding"},
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


def cleanup_expired_memories(db: Session, retention_days: int = 180) -> int:
    """
    清理超过保留期限的记忆记录。

    Args:
        db: 数据库会话
        retention_days: 保留天数，默认 180（半年）

    Returns:
        int: 删除行数
    """
    result = (
        db.query(UserMemoryEmbedding)
        .filter(
            text("created_at < NOW() - INTERVAL '1 day' * :retention_days")
            .bindparams(retention_days=retention_days)
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return result
