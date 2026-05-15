"""博客检索工具定义。

提供 search_blog Tool 的 schema 与完整执行逻辑。
根据用户查询检索语义最相似的博客文章。
"""

import logging
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from app.prompts.chat_prompts import BLOG_KNOWLEDGE_LABEL
from app.services.vector_search_service import BlogVectorSearchService

logger = logging.getLogger(__name__)


def _format_blog_knowledge(results: list) -> list[str]:
    """将博客检索结果格式化为文本块列表。"""
    if not results:
        return []
    formatted: list[str] = []
    for result in results:
        title = result.title or ""
        slug = result.slug or ""
        summary = result.summary or ""
        parts = [f"{BLOG_KNOWLEDGE_LABEL} {title}"]
        if slug:
            parts.append(f"链接：/blog/{slug}")
        if summary:
            parts.append(summary)
        formatted.append("\n".join(parts))
    return formatted


@tool
async def search_blog(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """根据用户查询检索语义最相似的博客文章。

    当用户询问博客、文章、作者写的技术内容、学习笔记等相关问题时调用。
    输入应为用户的原始问题或关键词，输出为最相关的博客文章片段。

    Args:
        query: 用户的搜索关键词或问题描述
    """
    db = config["configurable"].get("db")
    if db is None:
        logger.error("search_blog 缺少 db 依赖")
        return "博客检索服务配置错误。"

    try:
        blog_service = BlogVectorSearchService(db)
        blog_results = await blog_service.search(query, top_k=3)
        knowledge = _format_blog_knowledge(blog_results)
        content = "\n\n".join(knowledge) if knowledge else "未找到相关博客文章。"

        # 将来源信息写入 collector（如有），供调用节点收集
        sources = [
            {
                "post_id": r.post_id,
                "title": r.title,
                "similarity_score": r.similarity_score,
            }
            for r in blog_results
        ]
        collector = config["configurable"].get("_sources_collector")
        if collector is not None and isinstance(collector, list):
            collector.extend(sources)

        return content
    except Exception:
        logger.exception("博客向量检索失败")
        return "博客检索服务暂时不可用。"
