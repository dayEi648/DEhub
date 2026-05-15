"""博客检索工具定义。

提供 search_blog Tool 的 schema 与完整执行逻辑。
根据用户查询检索语义最相似的博客文章。
"""

import logging

from langchain_core.tools import tool

from app.db.session import SessionLocal
from app.services.blog_post_embedding_service import BlogPostEmbeddingService

logger = logging.getLogger(__name__)


@tool
async def search_blog(query: str) -> str:
    """检索 DE Hub 网站博客中与用户问题语义最相似的文章。

    当用户讨论的内容与 DE Hub 博客中的技术文章、学习笔记、教程高度相关时，
    或用户明确表示对网站中的博客文章感兴趣、要求推荐文章、询问具体技术主题时调用。

    输入应为用户的原始问题或关键词（保持中文），输出为格式化后的相关博客文章信息。

    Args:
        query: 用户的搜索关键词或问题描述
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = SessionLocal()
    try:
        blog_service = BlogPostEmbeddingService(db)
        blog_results = await blog_service.blog_post_embedding_search(
            query.strip(), top_k=3
        )

        if not blog_results:
            return "未找到与问题相关的博客文章。"

        parts = []
        for result in blog_results:
            lines = [f"【博客文章】{result.title}"]
            if result.slug:
                lines.append(f"链接：/blog/{result.slug}")
            if result.summary:
                lines.append(f"摘要：{result.summary}")
            lines.append(f"相似度：{result.similarity_score}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
    except Exception:
        logger.exception("博客向量检索失败")
        return "博客检索服务暂时不可用。"
    finally:
        db.close()
