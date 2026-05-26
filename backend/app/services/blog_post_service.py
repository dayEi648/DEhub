import asyncio
import logging

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.core.permission_levels import PermissionLevel
from app.models.user import User
from app.models.blog_post import BlogPost
from app.core.permissions import require_super_admin
from app.schemas.blog_post import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostResponse,
    BlogPostDetailResponse,
    BlogPostListItem,
    BlogPostListResponse,
)
from app.crud import blog_post as blog_post_crud
from app.utils.slug import generate_unique_slug
from app.storage.oss import upload_image, ImageUploadScene, convert_oss_url_to_file_path, extract_oss_image_urls_from_markdown
from app.services.oss_cleanup_service import OssCleanupService
import re

from app.infrastructure.llm_client import create_llm_small_client
from app.services.blog_post_embedding_service import BlogPostEmbeddingService
from app.infrastructure.cache import (
    build_cache_key,
    get_json_cache,
    set_json_cache,
    acquire_cache_lock,
    release_cache_lock,
)
from app.infrastructure.cache_invalidator import BlogCacheInvalidator
from app.core.config import settings
from app.prompts.blog_prompts import render_blog_summary_prompt
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class BlogPostService:
    def __init__(self, db: Session):
        self.db = db

    def _require_super_admin(self, current_user: User) -> None:
        """要求当前用户为超级管理员"""
        require_super_admin(current_user)

    def _ensure_slug_unique(self, slug: str, exclude_post_id: int | None = None) -> None:
        """校验 slug 唯一性"""
        existing = blog_post_crud.get_blog_post_by_slug(self.db, slug)
        if existing and (exclude_post_id is None or existing.id != exclude_post_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章 slug 已存在"
            )

    def _build_visible_query(self, current_user: User):
        """构建基于当前用户权限的可见文章查询基线（自动 join 分类与作者信息）"""
        query = (
            self.db.query(BlogPost)
            .options(joinedload(BlogPost.category), joinedload(BlogPost.user))
        )
        if current_user.permission < PermissionLevel.SUPER_ADMIN:
            query = query.filter(BlogPost.status == "published")
        return query

    # ---------- 写操作（超管专属）----------

    @staticmethod
    def _count_content_chars(content_md: str) -> int:
        """统计 Markdown 正文去除标记后的纯文本有效字符数（空白不计入）。"""
        text = content_md
        # 去除代码块
        text = re.sub(r'```[\s\S]*?```', '\n', text)
        # 去除行内代码
        text = re.sub(r'`[^`]*`', '', text)
        # 去除图片
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        # 去除链接（保留文本）
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        # 去除标题标记
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # 去除粗体/斜体标记
        text = re.sub(r'\*\*|__|\*|_', '', text)
        # 去除列表标记
        text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        # 去除引用标记
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
        # 去除水平线（支持前后空格）
        text = re.sub(r'^\s*-{3,}\s*$', '', text, flags=re.MULTILINE)
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 去除表格竖线分隔符
        text = re.sub(r'\|', ' ', text)
        # 将连续空白（换行、空格、制表符）压缩为单个空格，避免格式空白影响字数
        text = re.sub(r'\s+', ' ', text)
        return len(text.strip())

    async def _auto_generate_summary(self, content_md: str) -> str | None:
        """
        自动为长文生成摘要。仅在正文字数超过阈值时调用。
        失败时返回 None（不抛异常，避免阻塞创建/更新流程）。
        """
        system_prompt, user_prompt = render_blog_summary_prompt(
            content_md=content_md,
            min_length=settings.BLOG_SUMMARY_MIN_LENGTH,
            max_length=settings.BLOG_SUMMARY_MAX_LENGTH,
        )
        try:
            client = create_llm_small_client(timeout=settings.BLOG_SUMMARY_LLM_TIMEOUT)
            response = await client.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            summary = str(response.content).strip()
            if summary:
                return summary
        except Exception as e:
            logger.warning("AI 摘要生成失败: %s", e)
        return None

    async def create_blog_post(
        self, post_in: BlogPostCreate, current_user: User, file: UploadFile
    ) -> BlogPost:
        self._require_super_admin(current_user)

        # 强制为草稿，忽略前端传入的摘要
        post_in = post_in.model_copy(update={"status": "draft", "summary": None})

        # 若未提供 slug，根据标题自动生成
        if not post_in.slug:
            slug = generate_unique_slug(
                self.db, post_in.title, exists_checker=blog_post_crud.get_blog_post_by_slug
            )
            post_in = post_in.model_copy(update={"slug": slug})
        else:
            self._ensure_slug_unique(post_in.slug)

        # 根据正文长度自动判断是否需要生成摘要
        content_chars = self._count_content_chars(post_in.content_md)
        if content_chars > settings.BLOG_SUMMARY_CONTENT_THRESHOLD:
            summary = await self._auto_generate_summary(post_in.content_md)
            if summary:
                post_in = post_in.model_copy(update={"summary": summary})

        # 先上传再入库，避免上传失败时产生无效数据；若后续入库失败则清理新文件。
        cover_url = await upload_image(file, ImageUploadScene.cover)
        cleanup_service = OssCleanupService()

        try:
            db_post = blog_post_crud.create_blog_post(
                self.db,
                post_in,
                current_user.id,
                cover_image_url=cover_url,
            )
        except Exception:
            self.db.rollback()
            await cleanup_service.delete_file_after_commit(
                convert_oss_url_to_file_path(cover_url),
                source="blog.cover.rollback",
            )
            raise

        # 创建即 draft，无需生成向量嵌入

        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def publish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是发布状态")
        db_post.status = "published"
        self.db.commit()
        self.db.refresh(db_post)

        # 发布后同步生成向量嵌入
        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.sync_post_embedding, post_id)

        # 发布会影响公共列表和分类计数
        BlogCacheInvalidator.invalidate_all()

        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def unpublish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是草稿状态")
        db_post.status = "draft"
        self.db.commit()
        self.db.refresh(db_post)

        # 下架后同步清理向量嵌入
        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.delete_post_embedding, post_id)

        # 下线会影响公共列表和分类计数
        BlogCacheInvalidator.invalidate_all()

        # 重新查询以加载 category 关联，避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def update_blog_post(
        self, post_id: int, post_in: BlogPostUpdate, current_user: User, file: UploadFile | None = None
    ) -> BlogPost:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        update_data = post_in.model_dump(exclude_unset=True)

        # 禁止前端修改摘要和状态
        update_data.pop("summary", None)
        update_data.pop("status", None)

        # 如果正文发生实际变化，重新判断字数并生成/清除摘要
        new_content = update_data.get("content_md")
        if new_content is not None and new_content != db_post.content_md:
            content_chars = self._count_content_chars(new_content)
            if content_chars > settings.BLOG_SUMMARY_CONTENT_THRESHOLD:
                summary = await self._auto_generate_summary(new_content)
            else:
                summary = None
            update_data["summary"] = summary
            db_post.summary = summary  # 提前赋值，避免 CRUD 层覆盖

        # 重新构造 post_in（已去掉 status，并加入后端生成的 summary）
        post_in = BlogPostUpdate.model_validate(update_data)

        if "slug" in update_data and update_data["slug"] != db_post.slug:
            self._ensure_slug_unique(update_data["slug"], exclude_post_id=db_post.id)

        old_cover_url = db_post.cover_image_url
        new_cover_url: str | None = None
        cleanup_service = OssCleanupService()
        if file:
            new_cover_url = await upload_image(file, ImageUploadScene.cover)
            db_post.cover_image_url = new_cover_url

        try:
            updated = blog_post_crud.update_blog_post(self.db, db_post, post_in)
        except Exception:
            self.db.rollback()
            if new_cover_url:
                await cleanup_service.delete_file_after_commit(
                    convert_oss_url_to_file_path(new_cover_url),
                    source="blog.cover.rollback",
                )
            db_post.cover_image_url = old_cover_url
            raise

        if new_cover_url and old_cover_url:
            await cleanup_service.delete_file_after_commit(
                convert_oss_url_to_file_path(old_cover_url),
                source="blog.cover",
            )

        # 根据更新后的状态同步或删除向量嵌入
        embed_service = BlogPostEmbeddingService(self.db)
        if updated.status == "published":
            await asyncio.to_thread(embed_service.sync_post_embedding, updated.id)
        else:
            await asyncio.to_thread(embed_service.delete_post_embedding, updated.id)

        # 更新可能影响公共列表和分类计数
        BlogCacheInvalidator.invalidate_all()

        # 重新查询以加载 category 关联（可能已变更），避免延迟加载问题
        refreshed = blog_post_crud.get_blog_post_by_id(self.db, updated.id)
        return refreshed

    async def hard_delete_blog_post(self, post_id: int, current_user: User) -> None:
        self._require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        file_paths_to_delete: list[str] = []
        if db_post and db_post.cover_image_url:
            file_paths_to_delete.append(convert_oss_url_to_file_path(db_post.cover_image_url))

        # 级联清理正文中的内嵌 OSS 图片，实际删除在数据库删除成功后执行。
        if db_post and db_post.content_md:
            image_urls = extract_oss_image_urls_from_markdown(db_post.content_md)
            for url in image_urls:
                file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        # 硬删除前先清理向量嵌入（显式删除，不依赖数据库 CASCADE）
        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.delete_post_embedding, post_id)

        result = blog_post_crud.hard_delete_blog_post(self.db, post_id)
        if result == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        # 删除会影响公共列表和分类计数
        BlogCacheInvalidator.invalidate_all()

        cleanup_service = OssCleanupService()
        for file_path in file_paths_to_delete:
            await cleanup_service.delete_file_after_commit(
                file_path,
                source="blog.post.hard_delete",
            )

    # ---------- 读操作（权限区分）----------

    def _get_visible_post(self, current_user: User):
        """获取当前用户可见的单篇文章查询"""
        query = self.db.query(BlogPost)
        if current_user.permission < PermissionLevel.SUPER_ADMIN:
            query = query.filter(BlogPost.status == "published")
        return query

    def _build_detail_response(self, db_post: BlogPost, current_user: User) -> BlogPostDetailResponse:
        """组装博客详情响应（含相邻文章信息）。"""
        prev_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at < db_post.created_at)
            .order_by(BlogPost.created_at.desc())
            .first()
        )
        next_post = (
            self._build_visible_query(current_user)
            .filter(BlogPost.created_at > db_post.created_at)
            .order_by(BlogPost.created_at.asc())
            .first()
        )
        response_data = BlogPostResponse.model_validate(db_post).model_dump()
        response_data["prev_post"] = (
            BlogPostListItem.model_validate(prev_post) if prev_post else None
        )
        response_data["next_post"] = (
            BlogPostListItem.model_validate(next_post) if next_post else None
        )
        return BlogPostDetailResponse.model_validate(response_data)

    def get_blog_post(self, post_id: int, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.id == post_id).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        # 增加浏览量
        blog_post_crud.increment_view_count(self.db, post_id)
        self.db.refresh(db_post)

        return self._build_detail_response(db_post, current_user)

    def get_blog_post_by_slug(self, slug: str, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.slug == slug).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        # 增加浏览量
        blog_post_crud.increment_view_count(self.db, db_post.id)
        self.db.refresh(db_post)

        return self._build_detail_response(db_post, current_user)

    def list_blog_posts(
        self,
        skip: int,
        limit: int,
        status: str | None,
        category_id: int | None,
        tag: str | None,
        q: str | None,
        include_unpublished: bool,
        current_user: User,
    ) -> BlogPostListResponse:
        if current_user.permission != PermissionLevel.SUPER_ADMIN:
            effective_status = "published"
        else:
            effective_status = status if include_unpublished else "published"

        # 只有公共 published 列表才走缓存
        should_cache = effective_status == "published" and not include_unpublished

        cache_key = None
        ttl = None
        is_hot_key = False
        lock_acquired = False

        if should_cache:
            cache_params = {
                "skip": skip,
                "limit": limit,
                "status": "published",
                "category_id": category_id,
                "tag": tag,
                "q": q,
            }
            cache_key = build_cache_key("blog_posts:list", cache_params)

            if q:
                ttl = settings.CACHE_BLOG_LIST_TTL // 2  # 搜索场景 30s
            elif skip == 0 and limit == 6:
                ttl = settings.CACHE_BLOG_HOME_TTL  # 首页热门 120s
                is_hot_key = True
            else:
                ttl = settings.CACHE_BLOG_LIST_TTL  # 普通列表 60s

            cached = get_json_cache(cache_key, BlogPostListResponse)
            if cached is not None:
                return cached

            # 首页热门 key 加短锁防击穿
            if is_hot_key:
                lock_acquired = acquire_cache_lock(cache_key, ttl=5)

        posts = blog_post_crud.get_blog_posts(
            self.db,
            skip=skip,
            limit=limit,
            status=effective_status,
            category_id=category_id,
            tag=tag,
            q=q,
        )
        total = blog_post_crud.get_blog_posts_count(
            self.db,
            status=effective_status,
            category_id=category_id,
            tag=tag,
            q=q,
        )
        result = BlogPostListResponse(
            items=[BlogPostListItem.model_validate(post) for post in posts],
            total=total,
        )

        if should_cache and cache_key is not None and ttl is not None:
            # 热门 key 只有抢到锁才写缓存；普通 key 直接写
            if not is_hot_key or lock_acquired:
                set_json_cache(cache_key, result, ttl, tags=["blog_posts"])
            if lock_acquired:
                release_cache_lock(cache_key)

        return result


    # ---------- AI 辅助功能 ----------


