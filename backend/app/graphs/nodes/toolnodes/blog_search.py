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
async def search_blog(query: str, category_slug: str | None = None) -> str:
    """
    检索 DE Hub 网站博客中与用户问题语义最相似的文章。
    - 触发条件（满足任一即可调用）：
        a) 用户聊到了 编程技术、经验、AI 相关话题；
        b) 用户询问 DaiEe 写过什么、某技术话题的博客记录；
        c) 用户表达'想看看博客''有没有相关文章'等明确兴趣；
        d) 用户指定了某个分类，如"技术随笔下有没有 Docker 相关的文章"。
    - 非触发条件（禁止调用）：
        a) 用户闲聊、问候、提问无关技术的话题；
        b) 用户闲聊、问候、询问你的身份；
        c) 用户只是想了解有哪些博客分类（应使用 list_blog_categories）。
    - 调用后：结合检索结果组织自然语言回答，按需提供博客链接。

    Args:
        query: 用户的搜索关键词或问题描述
        category_slug: 可选，按博客分类 slug 过滤。当用户明确提到某个分类时使用，
                       如 "技术随笔"、"生活随想"。若不确定分类 slug，可先调用 list_blog_categories 查询。
    Returns:
        str: 格式化后的相关博客文章信息，包含文章标题、链接、摘要、相似度。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = SessionLocal()
    try:
        blog_service = BlogPostEmbeddingService(db)
        blog_results = await blog_service.blog_post_embedding_search_multi_query(
            query.strip(),
            category_slug=category_slug.strip() if category_slug else None,
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
            if result.category_name:
                lines.append(f"分类：{result.category_name}")
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
