"""OpenAPI 端点向量嵌入与检索服务。"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud import openapi_knowledge as crud
from app.infrastructure.embedding_client import get_embedding_client
from app.models.openapi_endpoint_embedding import OpenAPIEndpointEmbedding

logger = logging.getLogger(__name__)


class OpenAPIEmbeddingService:
    """OpenAPI 端点向量服务。

    负责将解析后的端点文本批量向量化入库，并提供语义检索能力。
    支持 content_hash 去重，避免无变化的重复 embedding API 调用。
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 向量入库
    # ------------------------------------------------------------------

    def sync_document_embeddings(self, document_id: int, chunks: list[dict]) -> int:
        """将解析后的端点分片批量向量化并入库。

        流程：
        1. 按 content_hash 去重，跳过已存在的端点
        2. 批量调用 embedding API
        3. 写入 pgvector

        Args:
            document_id: 文档 ID
            chunks: 解析后的端点分片列表

        Returns:
            实际入库的端点数量
        """
        if not chunks:
            return 0

        # 去重：只处理 content_hash 变化或新建的端点
        new_chunks: list[dict] = []
        existing_map: dict[str, OpenAPIEndpointEmbedding] = {}
        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            content_hash = chunk.get("content_hash", "")

            # 查询是否已存在相同 chunk_id 且 hash 未变
            existing = crud.get_endpoint_by_chunk_id(self.db, chunk_id)
            if existing is not None and existing.content_hash == content_hash:
                logger.debug("跳过重复端点: chunk_id=%s", chunk_id)
                continue
            new_chunks.append(chunk)
            if existing is not None:
                existing_map[chunk_id] = existing

        if not new_chunks:
            logger.info("所有端点均未变化，跳过 embedding: doc_id=%s", document_id)
            return 0

        # 批量 embedding
        texts = [chunk["content"] for chunk in new_chunks]
        try:
            embeddings = get_embedding_client().embed_documents(texts)
        except Exception:
            logger.exception("OpenAPI 端点批量 embedding 失败: doc_id=%s", document_id)
            raise

        if len(embeddings) != len(new_chunks):
            raise ValueError(
                "Embedding API 返回数量不匹配: expected=%s, got=%s"
                % (
                    len(new_chunks),
                    len(embeddings),
                )
            )

        # 入库
        inserted = 0
        for chunk, embedding in zip(new_chunks, embeddings):
            chunk_id = chunk["chunk_id"]
            existing = existing_map.get(chunk_id)
            try:
                if existing is None:
                    crud.create_endpoint_embedding(
                        db=self.db,
                        document_id=document_id,
                        chunk_id=chunk_id,
                        path=chunk["path"],
                        method=chunk["method"],
                        content=chunk["content"],
                        embedding=embedding,
                        content_hash=chunk.get("content_hash"),
                        summary=chunk.get("summary"),
                        description=chunk.get("description"),
                        tags=chunk.get("tags"),
                        operation_id=chunk.get("operation_id"),
                    )
                else:
                    crud.update_endpoint_embedding(
                        db=self.db,
                        endpoint=existing,
                        path=chunk["path"],
                        method=chunk["method"],
                        content=chunk["content"],
                        embedding=embedding,
                        content_hash=chunk.get("content_hash"),
                        summary=chunk.get("summary"),
                        description=chunk.get("description"),
                        tags=chunk.get("tags"),
                        operation_id=chunk.get("operation_id"),
                    )
                inserted += 1
            except Exception as exc:
                self.db.rollback()
                logger.exception("端点向量入库失败: chunk_id=%s", chunk_id)
                raise RuntimeError(f"端点向量入库失败: chunk_id={chunk_id}") from exc

        logger.info(
            "OpenAPI 向量同步完成: doc_id=%s, 新端点=%s, 入库=%s",
            document_id,
            len(new_chunks),
            inserted,
        )
        return inserted

    # ------------------------------------------------------------------
    # 向量检索
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float | None = None,
        method: str | None = None,
        document_id: int | None = None,
    ) -> list[dict]:
        """基于自然语言查询检索语义最相似的 OpenAPI 端点。

        Args:
            query: 用户查询文本
            top_k: 返回结果数量上限
            min_similarity: 最小相似度阈值，低于此值的结果会被过滤
            method: 可选 HTTP 方法过滤
            document_id: 可选文档 ID 过滤

        Returns:
            按相似度降序排列的结果列表，每条包含端点字段和 similarity_score
        """
        if not query or not query.strip():
            return []

        threshold = min_similarity if min_similarity is not None else settings.RAG_MIN_SIMILARITY

        try:
            query_embedding = get_embedding_client().embed_query(query)
        except Exception:
            logger.exception("OpenAPI 检索 embedding 失败")
            return []

        raw_results = crud.search_similar(
            self.db,
            query_embedding,
            top_k=top_k,
            method=method,
            document_id=document_id,
        )

        results: list[dict] = []
        for ep, distance in raw_results:
            similarity_score = max(0.0, 1.0 - float(distance))
            if similarity_score < threshold:
                continue
            results.append(
                {
                    "id": ep.id,
                    "document_id": ep.document_id,
                    "chunk_id": ep.chunk_id,
                    "path": ep.path,
                    "method": ep.method,
                    "summary": ep.summary,
                    "description": ep.description,
                    "tags": ep.tags,
                    "operation_id": ep.operation_id,
                    "content": ep.content,
                    "similarity_score": round(similarity_score, 4),
                }
            )

        return results
