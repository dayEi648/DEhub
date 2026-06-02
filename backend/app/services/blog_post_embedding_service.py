import asyncio
import hashlib
import logging

from sqlalchemy.orm import Session, joinedload
from app.crud import blog_post_embedding as embed_crud
from app.crud import blog_post as post_crud
from app.infrastructure.embedding_client import get_embedding_client
from app.core.config import settings
from app.models.blog_post import BlogPost
from app.schemas.blog_post_embedding import BlogPostSearchResult
from app.services.rag_query_service import RAGQueryService


logger = logging.getLogger(__name__)


class BlogPostEmbeddingService:
    """博客文章向量嵌入服务：拼接文本后向量化，按 content_hash 去重。"""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 私有工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _build_embedding_text(post) -> str:
        """拼接文章字段为待嵌入文本（超长时截断到最近句子边界）。"""
        parts = [f"标题：{post.title}"]

        if post.tags:
            tags_str = ", ".join(str(t) for t in post.tags)
            parts.append(f"标签：{tags_str}")

        if post.summary:
            parts.append(f"摘要：{post.summary}")
        else:
            parts.append(f"正文：{post.content_md}")

        text = "\n\n".join(parts)
        max_length = settings.BLOG_EMBEDDING_MAX_TEXT_LENGTH
        if len(text) > max_length:
            # 截断到最近的句子边界，避免语义断裂
            truncated = text[:max_length]
            # 从末尾向前查找句子结束符
            last_break = max(
                truncated.rfind("。"),
                truncated.rfind("."),
                truncated.rfind("\n"),
            )
            if last_break > 0:
                text = truncated[: last_break + 1]
            else:
                text = truncated
        return text

    @staticmethod
    def _compute_content_hash(text: str) -> str:
        """计算文本的 MD5 指纹（32 位十六进制字符串）。"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def sync_post_embedding(self, post_id: int) -> None:
        """同步指定文章的向量嵌入（仅处理 published 状态，异常不抛出）。"""
        try:
            post = post_crud.get_blog_post_by_id(self.db, post_id)
            if post is None:
                logger.warning("向量同步跳过：文章 %s 不存在或已删除", post_id)
                return

            if post.status != "published":
                logger.info(
                    "向量同步跳过：文章 %s 状态=%s",
                    post_id,
                    post.status,
                )
                return

            text = self._build_embedding_text(post)
            content_hash = self._compute_content_hash(text)

            # 检查现有 embedding 的 hash，避免无变化重复调用
            existing = embed_crud.get_embedding_by_post_id(self.db, post_id)
            if existing is not None and existing.content_hash == content_hash:
                logger.debug(
                    "向量同步跳过：文章 %s content_hash 未变化", post_id
                )
                return

            # 调用 embedding API
            embeddings = get_embedding_client().embed_documents([text])
            if not embeddings:
                logger.warning("Embedding API 返回空结果: post_id=%s", post_id)
                return
            embedding = embeddings[0]

            # 入库（插入或更新）
            embed_crud.upsert_embedding(
                db=self.db,
                post_id=post_id,
                embedding=embedding,
                content_hash=content_hash,
            )
            logger.info(
                "向量同步成功：文章 %s (%s)",
                post_id,
                "更新" if existing else "新建",
            )
        except Exception:
            logger.exception("向量同步失败：文章 %s", post_id)

    def blog_post_embedding_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float | None = None,
        category_slug: str | None = None,
    ) -> list[BlogPostSearchResult]:
        """检索语义最相似的博客文章。"""
        if not query or not query.strip():
            return []

        threshold = min_similarity if min_similarity is not None else settings.RAG_MIN_SIMILARITY

        try:
            query_embedding = get_embedding_client().embed_query(query)
        except Exception:
            logger.exception("Embedding query 失败")
            return []

        # 若提供了分类 slug，解析为 category_id 以在向量检索阶段过滤
        category_id = None
        if category_slug and category_slug.strip():
            from app.crud import blog_category as category_crud
            category = category_crud.get_category_by_slug(self.db, category_slug.strip())
            if category is not None:
                category_id = category.id

        raw_results = embed_crud.search_similar(
            self.db, query_embedding, top_k=top_k, category_id=category_id
        )

        # 批量预加载博客文章，消除 N+1 查询
        post_ids = [row.post_id for row, _ in raw_results if row.post_id]
        posts = (
            self.db.query(BlogPost)
            .options(joinedload(BlogPost.category))
            .filter(BlogPost.id.in_(post_ids))
            .all()
        ) if post_ids else []
        post_map = {p.id: p for p in posts}

        results: list[BlogPostSearchResult] = []
        for embedding_record, distance in raw_results:
            post = post_map.get(embedding_record.post_id)
            if not post:
                continue

            # 余弦距离转相似度分数：score = 1 - distance，范围 [0, 1]
            similarity_score = max(0.0, 1.0 - float(distance))
            if similarity_score < threshold:
                continue

            results.append(
                BlogPostSearchResult(
                    post_id=post.id,
                    title=post.title,
                    slug=post.slug,
                    summary=post.summary,
                    category_name=(post.category.name or "") if post.category else "",
                    similarity_score=round(similarity_score, 4),
                )
            )

        return results

    async def blog_post_embedding_search_multi_query(
        self,
        query: str,
        top_k: int | None = None,
        min_similarity: float | None = None,
        category_slug: str | None = None,
    ) -> list[BlogPostSearchResult]:
        """多查询并行检索：改写query后并发检索，合并去重并重排序。

        流程：
        1. 调用 RAGQueryService 将原始 query 改写为多条
        2. 并行 embedding + 向量检索
        3. 按 post_id 去重保留最高相似度
        4. 全局重排序后取 top_k

        Args:
            query: 用户原始查询
            top_k: 最终返回数量，默认读取 RAG_BLOG_TOP_K
            min_similarity: 相似度阈值，默认读取 RAG_MIN_SIMILARITY
            category_slug: 可选，按博客分类 slug 过滤

        Returns:
            list[BlogPostSearchResult]: 合并重排后的检索结果
        """
        if not query or not query.strip():
            return []

        effective_top_k = top_k if top_k is not None else settings.RAG_BLOG_TOP_K
        threshold = min_similarity if min_similarity is not None else settings.RAG_MIN_SIMILARITY
        per_query_top_k = settings.RAG_MULTI_QUERY_TOP_K_PER_QUERY

        # Step 1: Query 改写
        query_service = RAGQueryService()
        queries = await query_service.expand_queries(query.strip())

        if not queries:
            return []

        # 若改写被禁用且只有单条，降级走同步单查询（复用原有逻辑）
        if len(queries) == 1 and queries[0] == query.strip():
            return self.blog_post_embedding_search(
                query=query.strip(),
                top_k=effective_top_k,
                min_similarity=threshold,
                category_slug=category_slug,
            )

        # Step 2-3: 并行 embedding + 向量检索
        async def _search_single(q: str) -> list[BlogPostSearchResult]:
            """执行单条查询的完整检索流程（在线程池中运行阻塞调用）。"""
            try:
                query_embedding = await asyncio.to_thread(
                    get_embedding_client().embed_query, q
                )
            except Exception:
                logger.exception("Embedding query 失败: q=%s", q)
                return []

            # 解析 category_slug -> category_id
            category_id = None
            if category_slug and category_slug.strip():
                from app.crud import blog_category as category_crud
                category = category_crud.get_category_by_slug(
                    self.db, category_slug.strip()
                )
                if category is not None:
                    category_id = category.id

            raw_results = embed_crud.search_similar(
                self.db, query_embedding, top_k=per_query_top_k, category_id=category_id
            )

            # 批量预加载博客文章
            post_ids = [row.post_id for row, _ in raw_results if row.post_id]
            posts = (
                self.db.query(BlogPost)
                .options(joinedload(BlogPost.category))
                .filter(BlogPost.id.in_(post_ids))
                .all()
            ) if post_ids else []
            post_map = {p.id: p for p in posts}

            results: list[BlogPostSearchResult] = []
            for embedding_record, distance in raw_results:
                post = post_map.get(embedding_record.post_id)
                if not post:
                    continue
                similarity_score = max(0.0, 1.0 - float(distance))
                if similarity_score < threshold:
                    continue
                results.append(
                    BlogPostSearchResult(
                        post_id=post.id,
                        title=post.title,
                        slug=post.slug,
                        summary=post.summary,
                        category_name=(post.category.name or "") if post.category else "",
                        similarity_score=round(similarity_score, 4),
                    )
                )
            return results

        all_results = await asyncio.gather(*[_search_single(q) for q in queries])

        # Step 4-5: 合并去重 + 重排序
        merged = self._merge_and_rerank(all_results, effective_top_k)
        logger.info(
            "多查询检索完成: 原query='%s' -> %d 条query -> 合并后 %d 条结果",
            query.strip(), len(queries), len(merged),
        )
        return merged

    @staticmethod
    def _merge_and_rerank(
        results_list: list[list[BlogPostSearchResult]], top_k: int
    ) -> list[BlogPostSearchResult]:
        """合并多查询结果，按 post_id 去重保留最高相似度，再全局重排序。

        Args:
            results_list: 各查询的检索结果列表
            top_k: 最终取前 k 条

        Returns:
            list[BlogPostSearchResult]: 合并重排后的结果
        """
        best_by_post: dict[int, BlogPostSearchResult] = {}
        for results in results_list:
            for r in results:
                existing = best_by_post.get(r.post_id)
                if existing is None or r.similarity_score > existing.similarity_score:
                    best_by_post[r.post_id] = r

        sorted_results = sorted(
            best_by_post.values(), key=lambda x: x.similarity_score, reverse=True
        )
        return sorted_results[:top_k]

    def delete_post_embedding(self, post_id: int) -> None:
        """删除指定文章的向量嵌入记录（异常不抛出）。"""
        try:
            deleted = embed_crud.delete_embedding_by_post_id(self.db, post_id)
            if deleted:
                logger.info("向量删除成功：文章 %s", post_id)
            else:
                logger.debug("向量删除跳过：文章 %s 无向量记录", post_id)
        except Exception:
            logger.exception("向量删除失败：文章 %s", post_id)
