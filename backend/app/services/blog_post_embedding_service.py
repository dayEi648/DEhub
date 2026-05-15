import hashlib
import logging

from sqlalchemy.orm import Session, joinedload
from app.crud import blog_post_embedding as embed_crud
from app.crud import blog_post as post_crud
from app.infrastructure.embedding_client import get_embedding_client
from app.core.config import settings
from app.models.blog_post import BlogPost
from app.schemas.blog_post_embedding import BlogPostSearchResult


logger = logging.getLogger(__name__)

# 向量化文本的最大字符数（text-embedding-v4 上下文充裕的安全阈值）
_MAX_EMBEDDING_TEXT_LENGTH = 6000


class BlogPostEmbeddingService:
    """
    博客文章向量嵌入服务。

    负责将博客文章的标题、摘要、标签、正文拼接后向量化，
    并通过 content_hash 去重，避免无变化的重复 embedding API 调用。
    """

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # 私有工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _build_embedding_text(post) -> str:
        """
        将文章各字段拼接为待嵌入的单一文本。

        优先级：标题 > 摘要 > 标签 > 正文。
        超长时从正文尾部截断，确保标题和摘要一定保留。
        """
        parts = [f"标题：{post.title}"]

        if post.summary:
            parts.append(f"摘要：{post.summary}")

        if post.tags:
            tags_str = ", ".join(str(t) for t in post.tags)
            parts.append(f"标签：{tags_str}")

        parts.append(f"正文：{post.content_md}")

        text = "\n\n".join(parts)
        if len(text) > _MAX_EMBEDDING_TEXT_LENGTH:
            text = text[:_MAX_EMBEDDING_TEXT_LENGTH]
        return text

    @staticmethod
    def _compute_content_hash(text: str) -> str:
        """计算文本的 MD5 指纹（32 位十六进制字符串）。"""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------

    def sync_post_embedding(self, post_id: int) -> None:
        """
        同步指定文章的向量嵌入。

        流程：
        1. 查询文章（仅处理 published 且未删除的）
        2. 拼接文本并计算 content_hash
        3. 与现有向量记录的 content_hash 比对
        4. 若 hash 变化或不存在，调用 embedding API 并 upsert

        所有异常均被捕获并记录日志，不会抛异常中断调用方。

        Args:
            post_id: 文章 ID
        """
        try:
            post = post_crud.get_blog_post_by_id(self.db, post_id)
            if post is None:
                logger.warning("向量同步跳过：文章 %s 不存在或已删除", post_id)
                return

            if post.status != "published" or post.is_deleted:
                logger.info(
                    "向量同步跳过：文章 %s 状态=%s is_deleted=%s",
                    post_id,
                    post.status,
                    post.is_deleted,
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
            embedding = get_embedding_client().embed_documents([text])[0]

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

    async def blog_post_embedding_search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float | None = None, 
    ) -> list[BlogPostSearchResult]:
        """
        根据用户查询语句，检索语义最相似的博客文章。

        Args:
            query: 用户查询文本
            top_k: 返回结果数量上限
            min_similarity: 最小相似度阈值，低于此值的结果会被过滤

        Returns:
            list[BlogPostSearchResult]: 按相似度降序排列的结果列表
        """
        if not query or not query.strip():
            return []
        
        threshold = min_similarity if min_similarity is not None else settings.RAG_MIN_SIMILARITY

        query_embedding = await get_embedding_client().aembed_query(query)
        raw_results = embed_crud.search_similar(self.db, query_embedding, top_k=top_k)

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

    def delete_post_embedding(self, post_id: int) -> None:
        """
        删除指定文章的向量嵌入记录。

        异常被捕获并记录日志，不会抛异常中断调用方。

        Args:
            post_id: 文章 ID
        """
        try:
            deleted = embed_crud.delete_embedding_by_post_id(self.db, post_id)
            if deleted:
                logger.info("向量删除成功：文章 %s", post_id)
            else:
                logger.debug("向量删除跳过：文章 %s 无向量记录", post_id)
        except Exception:
            logger.exception("向量删除失败：文章 %s", post_id)
