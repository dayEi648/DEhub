import asyncio
import hashlib
import logging

from sqlalchemy.orm import Session

from app.crud.blog_post import get_blog_post_by_id
from app.crud.blog_post_embedding import (
    delete_embedding_by_post_id,
    get_embedding_by_post_id,
    upsert_embedding,
)
from app.db.session import SessionLocal
from app.infrastructure.embedding_client import get_embedding_client
from app.models.blog_post import BlogPost

logger = logging.getLogger(__name__)


def _build_embedding_text(post: BlogPost) -> str:
    """
    将博客文章及其分类、标签等信息组装成用于嵌入的纯文本。

    组装格式：
        标题: {title}
        分类: {category.name}
        标签: {tag1, tag2}
        摘要: {summary}
        正文: {content_md}

    Args:
        post: BlogPost 实例

    Returns:
        str: 组装后的文本
    """
    parts = []
    parts.append(f"标题: {post.title}")

    category_name = post.category.name if post.category else ""
    if category_name:
        parts.append(f"分类: {category_name}")

    if post.tags:
        parts.append(f"标签: {', '.join(post.tags)}")

    if post.summary:
        parts.append(f"摘要: {post.summary}")

    parts.append(f"正文: {post.content_md}")

    return "\n".join(parts)


def _compute_content_hash(text: str) -> str:
    """
    对文本计算 MD5 哈希，用于快速判断内容是否变化。

    Args:
        text: 待哈希的文本

    Returns:
        str: 32 位小写 MD5 字符串
    """
    return hashlib.md5(text.encode("utf-8")).hexdigest()


async def sync_blog_post_embedding(post_id: int) -> None:
    """
    异步后台任务：同步单篇博客文章的向量嵌入。

    流程：
    1. 查询文章（含分类）
    2. 若文章不存在 / 已软删除 / 非 published 状态 → 删除向量
    3. 组装嵌入文本并计算 content_hash
    4. 若 hash 未变化 → 跳过
    5. 调用 Embedding API 生成向量
    6. 写入/更新向量表

    Args:
        post_id: 博客文章 ID
    """
    db = SessionLocal()
    try:
        post = await asyncio.to_thread(get_blog_post_by_id, db, post_id)

        if not post or post.is_deleted or post.status != "published":
            deleted = await asyncio.to_thread(delete_embedding_by_post_id, db, post_id)
            if deleted:
                logger.info("已删除文章 %s 的向量记录", post_id)
            return

        text = _build_embedding_text(post)
        content_hash = _compute_content_hash(text)

        existing = await asyncio.to_thread(
            get_embedding_by_post_id, db, post_id
        )
        if existing and existing.content_hash == content_hash:
            logger.debug("文章 %s 内容未变化，跳过嵌入", post_id)
            return

        embedding = await get_embedding_client().aembed_single(text)

        await asyncio.to_thread(
            upsert_embedding, db, post_id, embedding, content_hash
        )
        logger.info("已同步文章 %s 的向量记录", post_id)

    except Exception:
        logger.exception("同步文章 %s 向量时出错", post_id)
    finally:
        await asyncio.to_thread(db.close)


async def sync_cleanup_orphaned_embeddings() -> None:
    """
    异步后台任务：清理向量表中已不存在对应博客文章（或文章已非 published / 已删除）的记录。

    通常由 cleanup_deleted_posts 后调用，作为防御性清理。
    """
    db = SessionLocal()
    try:
        from sqlalchemy import text as sa_text

        # 删除向量表中 post_id 在 blog_posts 中不存在或不符合条件的记录
        stmt = sa_text(
            """
            DELETE FROM blog_post_embeddings e
            WHERE NOT EXISTS (
                SELECT 1 FROM blog_posts p
                WHERE p.id = e.post_id
                  AND p.status = 'published'
                  AND p.is_deleted = FALSE
            )
            """
        )
        result = await asyncio.to_thread(db.execute, stmt)
        await asyncio.to_thread(db.commit)
        deleted_count = result.rowcount if hasattr(result, "rowcount") else 0
        if deleted_count:
            logger.info("已清理 %s 条孤立向量记录", deleted_count)
    except Exception:
        logger.exception("清理孤立向量记录时出错")
    finally:
        await asyncio.to_thread(db.close)


async def sync_all_published_posts() -> None:
    """
    一次性为所有已发布且未删除的博客文章生成/更新向量。

    适用于已有数据初始化或批量重同步。
    """
    db = SessionLocal()
    try:
        from sqlalchemy import select
        from app.models.blog_post import BlogPost

        stmt = select(BlogPost.id).where(
            BlogPost.status == "published",
            BlogPost.is_deleted == False,
        )
        rows = await asyncio.to_thread(db.execute, stmt)
        post_ids = [row.id for row in rows.scalars().all()]

        logger.info("开始批量同步 %s 篇文章的向量", len(post_ids))
        for post_id in post_ids:
            await sync_blog_post_embedding(post_id)
        logger.info("批量同步完成")
    except Exception:
        logger.exception("批量同步向量时出错")
    finally:
        await asyncio.to_thread(db.close)
