from sqlalchemy.orm import Session

from app.crud.blog_post_embedding import search_similar
from app.infrastructure.embedding_client import get_embedding_client
from app.schemas.blog_post_embedding import BlogPostSearchResult


class BlogVectorSearchService:
    """
    博客向量检索服务。

    为后续 RAG 模块提供基于语义相似度的博客文章检索能力。
    """

    def __init__(self, db: Session):
        self.db = db

    async def search(
        self, query: str, top_k: int = 5
    ) -> list[BlogPostSearchResult]:
        """
        根据用户查询语句，检索语义最相似的博客文章。

        Args:
            query: 用户查询文本
            top_k: 返回结果数量上限

        Returns:
            list[BlogPostSearchResult]: 按相似度降序排列的结果列表
        """
        if not query or not query.strip():
            return []

        query_embedding = await get_embedding_client().aembed_single(query)
        raw_results = search_similar(self.db, query_embedding, top_k=top_k)

        results: list[BlogPostSearchResult] = []
        for embedding_record, distance in raw_results:
            post = embedding_record.post
            if not post:
                continue

            # 余弦距离转相似度分数：score = 1 - distance，范围 [0, 1]
            similarity_score = max(0.0, 1.0 - float(distance))

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
