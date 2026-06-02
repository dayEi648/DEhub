"""博客分类列表工具定义。

提供 list_blog_categories Tool 的 schema 与完整执行逻辑。
当用户想先了解有哪些博客分类时调用，为后续条件检索提供分类信息。
"""

import logging

from langchain_core.tools import ToolException, tool

from app.crud import blog_category as blog_category_crud
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


@tool
def list_blog_categories() -> str:
    """
    列出 DE Hub 网站所有博客分类及其文章数量。

    触发条件：
    - 用户问"有哪些种类的博客"、"博客有哪些分类"、"网站有什么分类"
    - 用户不确定某个分类名称是否正确，想先查看全部分类

    非触发条件（禁止调用）：
    - 用户已经明确指定了分类，直接检索内容（应使用 search_blog）
    - 用户询问具体技术话题的博客文章（应使用 search_blog）

    返回结果供 LLM 和用户了解可用分类，后续可引导用户按分类检索博客。

    Returns:
        str: 格式化后的分类列表，包含分类名称、slug 和文章数量。
    """
    db = SessionLocal()
    try:
        categories = blog_category_crud.get_all_categories(db)
        if not categories:
            return "当前网站暂无博客分类。"

        lines = ["DE Hub 博客分类一览："]
        for cat in categories:
            post_count = blog_category_crud.count_posts_in_category(
                db, cat.id, status="published"
            )
            lines.append(
                f"【分类】{cat.name}（Slug: {cat.slug}）—— 已发布文章 {post_count} 篇"
            )
            if cat.description:
                lines.append(f"  简介：{cat.description}")

        return "\n".join(lines)
    except Exception as exc:
        logger.exception("列出博客分类失败")
        raise ToolException("博客分类列表获取失败，请稍后再试。") from exc
    finally:
        db.close()
