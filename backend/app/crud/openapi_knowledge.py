"""OpenAPI 知识库 CRUD 操作。"""

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.openapi_document import OpenAPIDocument
from app.models.openapi_endpoint_embedding import OpenAPIEndpointEmbedding
from pgvector.sqlalchemy import Vector


# ------------------------------------------------------------------
# 文档 CRUD
# ------------------------------------------------------------------


def create_document(
    db: Session,
    uploaded_by: int,
    filename: str,
    content_hash: str,
    status: str = "pending",
) -> OpenAPIDocument:
    """创建 OpenAPI 文档记录。

    Args:
        db: 数据库会话
        uploaded_by: 上传用户 ID
        filename: 原始文件名
        content_hash: 文件内容 MD5 hash
        status: 初始状态，默认 pending

    Returns:
        新建的 OpenAPIDocument 记录
    """
    doc = OpenAPIDocument(
        uploaded_by=uploaded_by,
        filename=filename,
        content_hash=content_hash,
        status=status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_document_by_id(db: Session, document_id: int) -> OpenAPIDocument | None:
    """按 ID 查询文档记录。"""
    return db.query(OpenAPIDocument).filter(OpenAPIDocument.id == document_id).first()


def get_document_by_content_hash(db: Session, content_hash: str) -> OpenAPIDocument | None:
    """按 content_hash 查询文档记录（用于重复上传检测）。"""
    return (
        db.query(OpenAPIDocument)
        .filter(OpenAPIDocument.content_hash == content_hash)
        .first()
    )


def list_documents(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
) -> tuple[list[OpenAPIDocument], int]:
    """分页查询文档列表，支持按状态过滤。

    Returns:
        (文档列表, 总数)
    """
    query = db.query(OpenAPIDocument)
    if status:
        query = query.filter(OpenAPIDocument.status == status)

    total = query.count()
    docs = (
        query.order_by(OpenAPIDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return docs, total


def update_document_status(
    db: Session,
    document_id: int,
    status: str,
    endpoint_count: int | None = None,
    chunk_count: int | None = None,
    error_message: str | None = None,
) -> OpenAPIDocument | None:
    """更新文档解析状态。

    Args:
        db: 数据库会话
        document_id: 文档 ID
        status: 新状态
        endpoint_count: 解析出的端点数量（可选）
        chunk_count: 写入向量的分片数量（可选）
        error_message: 失败原因（可选）

    Returns:
        更新后的记录，或 None（文档不存在）
    """
    doc = get_document_by_id(db, document_id)
    if doc is None:
        return None

    doc.status = status
    if endpoint_count is not None:
        doc.endpoint_count = endpoint_count
    if chunk_count is not None:
        doc.chunk_count = chunk_count
    if error_message is not None:
        doc.error_message = error_message

    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, document_id: int) -> bool:
    """删除文档及其级联端点向量。

    Args:
        db: 数据库会话
        document_id: 文档 ID

    Returns:
        是否成功删除（记录存在且被删除）
    """
    result = (
        db.query(OpenAPIDocument)
        .filter(OpenAPIDocument.id == document_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0


# ------------------------------------------------------------------
# 端点向量 CRUD
# ------------------------------------------------------------------


def create_endpoint_embedding(
    db: Session,
    document_id: int,
    chunk_id: str,
    path: str,
    method: str,
    content: str,
    embedding: list[float],
    content_hash: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
) -> OpenAPIEndpointEmbedding:
    """创建端点向量记录。

    Args:
        db: 数据库会话
        document_id: 所属文档 ID
        chunk_id: 端点分片唯一 ID
        path: API 路径
        method: HTTP 方法
        content: 用于 RAG 的端点文本
        embedding: 向量
        content_hash: 端点内容 hash（可选）
        summary: OpenAPI summary（可选）
        description: OpenAPI description（可选）
        tags: 标签列表（可选）
        operation_id: OpenAPI operationId（可选）

    Returns:
        新建的 OpenAPIEndpointEmbedding 记录
    """
    ep = OpenAPIEndpointEmbedding(
        document_id=document_id,
        chunk_id=chunk_id,
        path=path,
        method=method.upper(),
        content=content,
        embedding=embedding,
        content_hash=content_hash,
        summary=summary,
        description=description,
        tags=tags,
        operation_id=operation_id,
    )
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return ep


def get_endpoint_by_chunk_id(
    db: Session, chunk_id: str
) -> OpenAPIEndpointEmbedding | None:
    """按 chunk_id 查询端点向量记录。"""
    return (
        db.query(OpenAPIEndpointEmbedding)
        .filter(OpenAPIEndpointEmbedding.chunk_id == chunk_id)
        .first()
    )


def update_endpoint_embedding(
    db: Session,
    endpoint: OpenAPIEndpointEmbedding,
    *,
    path: str,
    method: str,
    content: str,
    embedding: list[float],
    content_hash: str | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    operation_id: str | None = None,
) -> OpenAPIEndpointEmbedding:
    """更新已有端点向量记录。"""
    endpoint.path = path
    endpoint.method = method.upper()
    endpoint.content = content
    endpoint.embedding = embedding
    endpoint.content_hash = content_hash
    endpoint.summary = summary
    endpoint.description = description
    endpoint.tags = tags
    endpoint.operation_id = operation_id
    db.commit()
    db.refresh(endpoint)
    return endpoint


def list_endpoints(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    document_id: int | None = None,
    method: str | None = None,
    tag: str | None = None,
) -> tuple[list[OpenAPIEndpointEmbedding], int]:
    """分页查询端点列表，支持按文档、方法、标签过滤。

    Returns:
        (端点列表, 总数)
    """
    query = db.query(OpenAPIEndpointEmbedding)

    if document_id is not None:
        query = query.filter(OpenAPIEndpointEmbedding.document_id == document_id)
    if method is not None:
        query = query.filter(
            OpenAPIEndpointEmbedding.method == method.upper()
        )
    if tag is not None:
        query = query.filter(
            OpenAPIEndpointEmbedding.tags.contains([tag])
        )

    total = query.count()
    eps = (
        query.order_by(OpenAPIEndpointEmbedding.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return eps, total


def delete_endpoint_by_id(db: Session, endpoint_id: int) -> bool:
    """按 ID 删除单个端点向量记录。

    Args:
        db: 数据库会话
        endpoint_id: 端点 ID

    Returns:
        是否成功删除
    """
    result = (
        db.query(OpenAPIEndpointEmbedding)
        .filter(OpenAPIEndpointEmbedding.id == endpoint_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return result > 0


def search_similar(
    db: Session,
    query_embedding: list[float],
    top_k: int = 5,
    method: str | None = None,
    document_id: int | None = None,
) -> list[tuple[OpenAPIEndpointEmbedding, float]]:
    """基于余弦距离检索最相似的 OpenAPI 端点向量。

    使用 pgvector 的 ``<=>``（余弦距离）算子，距离越小越相似。
    返回结果按距离升序排列。

    Args:
        db: 数据库会话
        query_embedding: 查询向量
        top_k: 返回结果数量上限
        method: 可选 HTTP 方法过滤
        document_id: 可选文档 ID 过滤

    Returns:
        list[tuple[OpenAPIEndpointEmbedding, float]]: (向量记录, 距离) 列表
    """
    where_clauses = []
    params: dict = {
        "embedding": query_embedding,
        "top_k": top_k,
    }

    if method is not None:
        where_clauses.append("method = :method")
        params["method"] = method.upper()
    if document_id is not None:
        where_clauses.append("document_id = :document_id")
        params["document_id"] = document_id

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    stmt = text(
        f"""
        SELECT id, document_id, chunk_id, path, method, summary, description,
               tags, operation_id, content, embedding, content_hash, created_at, updated_at,
               embedding <=> :embedding AS distance
        FROM openapi_endpoint_embeddings
        {where_sql}
        ORDER BY embedding <=> :embedding
        LIMIT :top_k
        """
    ).bindparams(
        bindparam("embedding", query_embedding, type_=Vector(settings.EMBEDDING_DIMENSION_EFFECTIVE)),
        **{k: v for k, v in params.items() if k != "embedding"},
    )

    rows = db.execute(stmt).all()

    results: list[tuple[OpenAPIEndpointEmbedding, float]] = []
    for row in rows:
        ep = OpenAPIEndpointEmbedding(
            id=row.id,
            document_id=row.document_id,
            chunk_id=row.chunk_id,
            path=row.path,
            method=row.method,
            summary=row.summary,
            description=row.description,
            tags=row.tags,
            operation_id=row.operation_id,
            content=row.content,
            embedding=row.embedding,
            content_hash=row.content_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        results.append((ep, float(row.distance)))

    return results
