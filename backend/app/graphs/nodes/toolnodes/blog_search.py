"""博客检索工具定义。

提供 search_blog Tool 的 schema 与完整执行逻辑。
根据用户查询检索语义最相似的博客文章。
"""

import logging

from langchain_core.tools import ToolException, tool

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.blog_post_embedding_service import BlogPostEmbeddingService

logger = logging.getLogger(__name__)


@tool
def search_blog(query: str) -> str:
    """
    检索 DE Hub 网站博客中与用户问题语义最相似的文章。\n
    - 触发条件（满足任一即可调用）：\n
        a) 用户聊到了 编程技术、经验、AI 相关话题；\n
        b) 用户询问 DaiEe 写过什么、某技术话题的博客记录；\n
        c) 用户表达'想看看博客''有没有相关文章'等明确兴趣。\n
    - 非触发条件（禁止调用）：\n
        a) 用户闲聊、问候、提问无关技术的话题；\n
        b) 用户闲聊、问候、询问你的身份。\n
    - 调用后：结合检索结果组织自然语言回答，按需提供博客链接。\n\n

    Args:
        query: 用户的搜索关键词或问题描述
    Returns:
        str: 格式化后的相关博客文章信息，包含文章标题、链接、摘要、相似度。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = SessionLocal()
    try:
        blog_service = BlogPostEmbeddingService(db)
        blog_results = blog_service.blog_post_embedding_search(
            query.strip(), top_k=settings.RAG_BLOG_TOP_K
        )

        if not blog_results:
            return "未找到与问题相关的博客文章。"

        parts = []
        for result in blog_results:
            lines = [f"【博客文章】{result.title}"]
            if result.slug:
                path = settings.FRONTEND_BLOG_DETAIL_PATH.format(slug=result.slug)
                lines.append(f"链接：{path}")
                lines.append(f"Slug: {result.slug}")
            if result.summary:
                lines.append(f"摘要：{result.summary}")
            lines.append(f"相似度：{result.similarity_score:.4f}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
    except Exception as exc:
        logger.exception("博客向量检索失败")
        raise ToolException("博客检索服务暂时不可用。") from exc
    finally:
        db.close()
