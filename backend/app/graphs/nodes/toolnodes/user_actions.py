"""用户操作类工具定义（供 LLM Tool Calling 使用）。

涉及用户个人的收藏、关注、内容查看等操作。
所有工具内部通过 _context.current_user_id_var 获取当前用户 ID。
"""

import logging

from fastapi import HTTPException
from langchain_core.tools import tool

from app.crud import blog_post as blog_post_crud
from app.crud import forum_zone as forum_zone_crud
from app.crud import user_favorite as favorite_crud
from app.db.session import SessionLocal
from app.graphs.nodes.toolnodes._context import current_user_id_var
from app.services.user_favorite_service import UserFavoriteService

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 博客收藏
# ------------------------------------------------------------------

@tool
def favorite_blog_post(slug: str) -> str:
    """
    帮用户收藏一篇博客文章。

    当用户明确表示"收藏这篇博客"、"把这篇文章加入收藏"、"帮我收藏一下"等时调用。
    参数 slug 应从 search_blog 返回结果中的 "Slug: xxx" 行获取。

    Args:
        slug: 博客文章的 slug 标识，如 "docker-best-practices"
    Returns:
        str: 操作结果提示
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        service = UserFavoriteService(db)
        service.favorite_blog_post_by_slug(slug, user_id)
        return "收藏成功。"
    except HTTPException as exc:
        return f"操作失败：{exc.detail}"
    except Exception:
        logger.exception("收藏博客失败: slug=%s user=%s", slug, user_id)
        return "收藏服务暂时不可用，请稍后再试。"
    finally:
        db.close()


@tool
def unfavorite_blog_post(slug: str) -> str:
    """
    帮用户取消收藏一篇博客文章。

    当用户明确表示"取消收藏这篇博客"、"把这篇文章移出收藏"等时调用。
    参数 slug 应从 search_blog 返回结果或 list_my_blog_favorites 返回结果中获取。

    Args:
        slug: 博客文章的 slug 标识
    Returns:
        str: 操作结果提示
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        service = UserFavoriteService(db)
        service.unfavorite_blog_post_by_slug(slug, user_id)
        return "已取消收藏。"
    except HTTPException as exc:
        return f"操作失败：{exc.detail}"
    except Exception:
        logger.exception("取消收藏博客失败: slug=%s user=%s", slug, user_id)
        return "取消收藏服务暂时不可用，请稍后再试。"
    finally:
        db.close()


# ------------------------------------------------------------------
# 论坛分区
# ------------------------------------------------------------------

@tool
def list_forum_zones() -> str:
    """
    列出 DE Hub 网站的所有论坛分区。

    当用户问"有哪些论坛分区"、"论坛有哪些版块"、"网站有哪些讨论区"等时调用。
    返回结果中包含每个分区的 ID、名称和简述，供后续 follow_forum_zone / unfollow_forum_zone 使用。

    Returns:
        str: 格式化后的论坛分区列表
    """
    db = SessionLocal()
    try:
        zones = forum_zone_crud.get_all_zones(db)
        if not zones:
            return "当前网站暂无论坛分区。"

        lines = []
        for zone in zones:
            desc = zone.description or "暂无描述"
            lines.append(
                f"【论坛分区】ID: {zone.id}, 名称: {zone.zone_name}, 简述: {desc}"
            )
        return "\n".join(lines)
    except Exception:
        logger.exception("列出论坛分区失败")
        return "论坛分区列表获取失败，请稍后再试。"
    finally:
        db.close()


@tool
def follow_forum_zone(zone_id: int) -> str:
    """
    帮用户关注一个论坛分区。

    当用户说"关注 React 分区"、"帮我关注这个版块"等时调用。
    参数 zone_id 应从 list_forum_zones 返回结果中的 "ID: xxx" 获取。

    Args:
        zone_id: 论坛分区的数字 ID
    Returns:
        str: 操作结果提示
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        service = UserFavoriteService(db)
        service.follow_zone_by_id(zone_id, user_id)
        return "关注成功。"
    except HTTPException as exc:
        return f"操作失败：{exc.detail}"
    except Exception:
        logger.exception("关注分区失败: zone_id=%s user=%s", zone_id, user_id)
        return "关注服务暂时不可用，请稍后再试。"
    finally:
        db.close()


@tool
def unfollow_forum_zone(zone_id: int) -> str:
    """
    帮用户取消关注一个论坛分区。

    当用户说"取消关注 React 分区"、"取消关注这个版块"等时调用。
    参数 zone_id 应从 list_forum_zones 或 list_my_zone_follows 返回结果中获取。

    Args:
        zone_id: 论坛分区的数字 ID
    Returns:
        str: 操作结果提示
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        service = UserFavoriteService(db)
        service.unfollow_zone_by_id(zone_id, user_id)
        return "已取消关注。"
    except HTTPException as exc:
        return f"操作失败：{exc.detail}"
    except Exception:
        logger.exception("取消关注分区失败: zone_id=%s user=%s", zone_id, user_id)
        return "取消关注服务暂时不可用，请稍后再试。"
    finally:
        db.close()


# ------------------------------------------------------------------
# 博客详情与收藏列表
# ------------------------------------------------------------------

@tool
def get_blog_post_detail(slug: str) -> str:
    """
    获取某篇博客文章的完整正文内容。

    当用户说"把那篇博客的完整内容给我看看"、"详细讲讲这篇文章"、"把正文发给我"等时调用。
    返回结果中只包含标题和正文，不包含 id、作者、浏览量等不必要信息。

    Args:
        slug: 博客文章的 slug 标识
    Returns:
        str: 博客标题和完整正文
    """
    db = SessionLocal()
    try:
        post = blog_post_crud.get_blog_post_by_slug(db, slug)
        if not post or post.status != "published":
            return "未找到该博客文章，或文章尚未发布。"

        parts = [f"【博客标题】{post.title}\n", "【正文】", post.content_md]
        return "\n".join(parts)
    except Exception:
        logger.exception("获取博客详情失败: slug=%s", slug)
        return "博客详情获取失败，请稍后再试。"
    finally:
        db.close()


@tool
def list_my_blog_favorites() -> str:
    """
    列出当前用户收藏的所有博客文章。

    当用户问"我收藏了哪些博客"、"我有哪些收藏的文章"等时调用。
    返回结果中每行包含文章标题和 Slug（供你内部使用），向用户展示时只展示标题。

    Returns:
        str: 格式化后的收藏博客列表
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        items, total = favorite_crud.get_user_blog_post_favorites(
            db, user_id=user_id, skip=0, limit=100, status="published"
        )
        if not items:
            return "你还没有收藏任何博客文章。"

        lines = [f"你收藏的博客文章（共 {total} 篇）："]
        for idx, post in enumerate(items, 1):
            lines.append(f"{idx}. {post.title}（Slug: {post.slug}）")
        return "\n".join(lines)
    except Exception:
        logger.exception("获取博客收藏列表失败: user=%s", user_id)
        return "收藏列表获取失败，请稍后再试。"
    finally:
        db.close()


@tool
def list_my_zone_follows() -> str:
    """
    列出当前用户关注的所有论坛分区。

    当用户问"我关注了哪些分区"、"我关注了哪些版块"等时调用。
    返回结果中每行包含分区名称和 ID（供你内部使用），向用户展示时只展示名称。

    Returns:
        str: 格式化后的关注分区列表
    """
    user_id = current_user_id_var.get()
    if not user_id:
        return "错误：无法获取当前用户身份，请确认已登录。"

    db = SessionLocal()
    try:
        items, total = favorite_crud.get_user_zone_follows(
            db, user_id=user_id, skip=0, limit=100
        )
        if not items:
            return "你还没有关注任何论坛分区。"

        lines = [f"你关注的论坛分区（共 {total} 个）："]
        for idx, zone in enumerate(items, 1):
            lines.append(f"{idx}. {zone.zone_name}（ID: {zone.id}）")
        return "\n".join(lines)
    except Exception:
        logger.exception("获取分区关注列表失败: user=%s", user_id)
        return "关注列表获取失败，请稍后再试。"
    finally:
        db.close()
