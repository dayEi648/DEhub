"""
向量知识库存储封装。
基于 pgvector + asyncpg 原生 SQL，操作 echovector 数据库的 kb_documents 表。
"""
import json
import uuid
from typing import Optional

from app.config import settings
from app.services.embedding_service import embedding_service, EmbeddingError
from app.utils.async_db import db_pools


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


class VectorStoreError(Exception):
    """向量存储异常。"""

    pass


class VectorStore:
    """向量存储服务，提供文档入库、检索、删除能力。"""

    @staticmethod
    def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
        """
        按固定长度切分文本，相邻块保留重叠区域。

        :param text: 原始文本
        :param chunk_size: 每块最大字符数
        :param overlap: 相邻块重叠字符数
        :return: 文本块列表
        """
        if not text:
            return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunks.append(text[start:end])
            if end == text_len:
                break
            start = end - overlap
        return chunks

    async def add_document(
        self,
        title: str,
        content: str,
        source_type: str = "manual_upload",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        将文档切分、生成 Embedding 后写入 kb_documents。

        :param title: 文档标题
        :param content: 文档全文内容
        :param source_type: 来源类型（默认 manual_upload）
        :param metadata: 附加元数据（原始文件名、上传者等）
        :return: {"doc_id": str, "total_chunks": int}
        :raises EmbeddingError: Embedding 调用失败
        :raises ValueError: 内容为空
        """
        if not content or not content.strip():
            raise ValueError("文档内容不能为空")

        doc_id = uuid.uuid4().hex
        chunks = self._split_text(content.strip())
        if not chunks:
            raise ValueError("文档切分后无有效内容")

        # 批量生成 embedding
        try:
            embeddings = await embedding_service.aembed_texts(chunks)
        except EmbeddingError:
            raise

        meta = metadata or {}
        total_chunks = len(chunks)
        meta_json = json.dumps(meta, ensure_ascii=False)

        async with db_pools.echovector.acquire() as conn:
            for idx, (chunk_text, emb) in enumerate(zip(chunks, embeddings)):
                emb_str = "[" + ",".join(str(v) for v in emb) + "]"
                await conn.execute(
                    """
                    INSERT INTO kb_documents
                        (doc_id, source_type, title, content, metadata, chunk_index, total_chunks, embedding)
                    VALUES
                        ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::vector)
                    """,
                    doc_id,
                    source_type,
                    title,
                    chunk_text,
                    meta_json,
                    idx,
                    total_chunks,
                    emb_str,
                )

        return {"doc_id": doc_id, "total_chunks": total_chunks}

    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        对查询文本做 Embedding，在 kb_documents 中做向量相似度搜索。

        :param query: 查询文本
        :param top_k: 返回结果数（默认 5，最大 20）
        :return: 检索结果列表，每条包含 doc_id, title, content, similarity, metadata
        :raises EmbeddingError: Embedding 调用失败
        """
        if top_k < 1:
            top_k = 1
        if top_k > 20:
            top_k = 20

        try:
            query_embedding = await embedding_service.aembed_query(query)
        except EmbeddingError:
            raise

        query_emb_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        async with db_pools.echovector.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    doc_id,
                    title,
                    content,
                    metadata,
                    1 - (embedding <=> $1::vector) AS similarity
                FROM kb_documents
                WHERE is_deleted = FALSE
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                query_emb_str,
                top_k,
            )

        results = []
        for row in rows:
            meta = row["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            elif meta is None:
                meta = {}
            results.append({
                "doc_id": row["doc_id"],
                "title": row["title"],
                "content": row["content"],
                "similarity": round(float(row["similarity"]), 4),
                "metadata": meta,
            })
        return results

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """
        软删除指定 doc_id 的所有分块。

        :param doc_id: 文档 ID
        :return: 被删除的分块数量
        """
        async with db_pools.echovector.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE kb_documents
                SET is_deleted = TRUE
                WHERE doc_id = $1 AND is_deleted = FALSE
                """,
                doc_id,
            )
        # asyncpg execute 返回类似 "UPDATE 3" 的字符串
        try:
            return int(result.split()[-1])
        except (IndexError, ValueError):
            return 0

    async def get_document_chunks(self, doc_id: str) -> list[dict]:
        """
        获取指定文档的所有分块（不含 embedding 向量）。

        :param doc_id: 文档 ID
        :return: 分块列表
        """
        async with db_pools.echovector.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    id, doc_id, source_type, title, content,
                    metadata, chunk_index, total_chunks, create_time
                FROM kb_documents
                WHERE doc_id = $1 AND is_deleted = FALSE
                ORDER BY chunk_index
                """,
                doc_id,
            )
        return [
            {
                "id": row["id"],
                "doc_id": row["doc_id"],
                "source_type": row["source_type"],
                "title": row["title"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
                "chunk_index": row["chunk_index"],
                "total_chunks": row["total_chunks"],
                "create_time": row["create_time"].isoformat() if row["create_time"] else None,
            }
            for row in rows
        ]


    async def list_documents(
        self,
        page_num: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """
        分页查询知识库文档列表（按 doc_id 去重）。

        :param page_num: 页码（从 1 开始）
        :param page_size: 每页条数
        :return: (文档列表, 总条数)
        """
        offset = (page_num - 1) * page_size
        async with db_pools.echovector.acquire() as conn:
            # 去重统计
            total_row = await conn.fetchrow(
                """
                SELECT COUNT(DISTINCT doc_id) AS total
                FROM kb_documents
                WHERE is_deleted = FALSE
                """
            )
            total = total_row["total"] if total_row else 0

            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (doc_id)
                    doc_id,
                    title,
                    source_type,
                    metadata,
                    total_chunks,
                    create_time
                FROM kb_documents
                WHERE is_deleted = FALSE
                ORDER BY doc_id, create_time DESC
                LIMIT $1 OFFSET $2
                """,
                page_size,
                offset,
            )

        docs = []
        for row in rows:
            meta = row["metadata"]
            if isinstance(meta, str):
                meta = json.loads(meta)
            elif meta is None:
                meta = {}
            docs.append({
                "doc_id": row["doc_id"],
                "title": row["title"],
                "source_type": row["source_type"],
                "total_chunks": row["total_chunks"],
                "metadata": meta,
                "create_time": row["create_time"].isoformat() if row["create_time"] else None,
            })
        return docs, total


# 全局单例
vector_store = VectorStore()
