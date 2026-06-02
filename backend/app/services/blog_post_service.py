import asyncio
import logging
import re

from fastapi import HTTPException, status, UploadFile
from sqlalchemy import and_, or_
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
from app.crud import blog_category as blog_category_crud
from app.utils.slug import generate_unique_slug
from app.utils.text import extract_plain_text_summary
from app.storage.oss import upload_image, ImageUploadScene, convert_oss_url_to_file_path, extract_oss_image_urls_from_markdown
from app.services.oss_cleanup_service import OssCleanupService
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

    def _ensure_slug_unique(self, slug: str, exclude_post_id: int | None = None) -> None:
        existing = blog_post_crud.get_blog_post_by_slug(self.db, slug)
        if existing and (exclude_post_id is None or existing.id != exclude_post_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文章 slug 已存在"
            )

    def _build_visible_query(self, current_user: User):
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
        text = content_md
        text = re.sub(r'```[\s\S]*?```', '\n', text)
        text = re.sub(r'`[^`]*`', '', text)
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*|__|\*|_', '', text)
        text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^>\s?', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*-{3,}\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\|', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return len(text.strip())

    async def _auto_generate_summary(self, content_md: str) -> str | None:
        """自动为长文生成摘要。失败返回 None，不阻塞流程。"""
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
        require_super_admin(current_user)

        post_in = post_in.model_copy(update={"status": "draft", "summary": None})

        category = blog_category_crud.get_category_by_id(self.db, post_in.category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")

        if not post_in.slug:
            slug = generate_unique_slug(
                self.db, post_in.title, exists_checker=blog_post_crud.get_blog_post_by_slug
            )
            post_in = post_in.model_copy(update={"slug": slug})
        else:
            self._ensure_slug_unique(post_in.slug)

        content_chars = self._count_content_chars(post_in.content_md)
        if content_chars > settings.BLOG_SUMMARY_CONTENT_THRESHOLD:
            summary = await self._auto_generate_summary(post_in.content_md)
            if summary:
                post_in = post_in.model_copy(update={"summary": summary})

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

        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def publish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是发布状态")
        db_post.status = "published"
        self.db.commit()
        self.db.refresh(db_post)

        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.sync_post_embedding, post_id)

        BlogCacheInvalidator.invalidate_all()

        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def unpublish_blog_post(self, post_id: int, current_user: User) -> BlogPost:
        require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")
        if db_post.status == "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="文章已是草稿状态")
        db_post.status = "draft"
        self.db.commit()
        self.db.refresh(db_post)

        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.delete_post_embedding, post_id)

        BlogCacheInvalidator.invalidate_all()

        refreshed = blog_post_crud.get_blog_post_by_id(self.db, db_post.id)
        return refreshed

    async def update_blog_post(
        self, post_id: int, post_in: BlogPostUpdate, current_user: User, file: UploadFile | None = None
    ) -> BlogPost:
        require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        update_data = post_in.model_dump(exclude_unset=True)
        update_data.pop("summary", None)
        update_data.pop("status", None)

        if "category_id" in update_data and update_data["category_id"] != db_post.category_id:
            category = blog_category_crud.get_category_by_id(self.db, update_data["category_id"])
            if not category:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")

        new_content = update_data.get("content_md")
        if new_content is not None and new_content != db_post.content_md:
            content_chars = self._count_content_chars(new_content)
            if content_chars > settings.BLOG_SUMMARY_CONTENT_THRESHOLD:
                summary = await self._auto_generate_summary(new_content)
            else:
                summary = None
            update_data["summary"] = summary
            db_post.summary = summary

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

        embed_service = BlogPostEmbeddingService(self.db)
        if updated.status == "published":
            await asyncio.to_thread(embed_service.sync_post_embedding, updated.id)
        else:
            await asyncio.to_thread(embed_service.delete_post_embedding, updated.id)

        BlogCacheInvalidator.invalidate_all()

        refreshed = blog_post_crud.get_blog_post_by_id(self.db, updated.id)
        return refreshed

    async def hard_delete_blog_post(self, post_id: int, current_user: User) -> None:
        require_super_admin(current_user)
        db_post = blog_post_crud.get_blog_post_by_id(self.db, post_id)
        file_paths_to_delete: list[str] = []
        if db_post and db_post.cover_image_url:
            file_paths_to_delete.append(convert_oss_url_to_file_path(db_post.cover_image_url))

        if db_post and db_post.content_md:
            image_urls = extract_oss_image_urls_from_markdown(db_post.content_md)
            for url in image_urls:
                file_paths_to_delete.append(convert_oss_url_to_file_path(url))

        embed_service = BlogPostEmbeddingService(self.db)
        await asyncio.to_thread(embed_service.delete_post_embedding, post_id)

        # 清理关联评论及评论点赞（与文章删除在同一事务中）
        from app.crud import comment as comment_crud

        comment_ids = comment_crud.get_comment_ids_by_target_ids(
            self.db, target_type="blog_post", target_ids=[post_id]
        )
        if comment_ids:
            comment_crud.delete_comment_likes_by_comment_ids(
                self.db, comment_ids, auto_commit=False
            )
            comment_crud.delete_comments_by_ids(
                self.db, comment_ids, auto_commit=False
            )

        result = blog_post_crud.hard_delete_blog_post(self.db, post_id)
        if result == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        BlogCacheInvalidator.invalidate_all()

        cleanup_service = OssCleanupService()
        for file_path in file_paths_to_delete:
            await cleanup_service.delete_file_after_commit(
                file_path,
                source="blog.post.hard_delete",
            )

    # ---------- 读操作（权限区分）----------

    def _get_visible_post(self, current_user: User):
        query = self.db.query(BlogPost)
        if current_user.permission < PermissionLevel.SUPER_ADMIN:
            query = query.filter(BlogPost.status == "published")
        return query

    def _build_list_item(self, post: BlogPost) -> BlogPostListItem:
        """构建列表项，若 summary 为空则自动从正文截取纯文本摘要。"""
        item = BlogPostListItem.model_validate(post)
        if not item.summary and post.content_md:
            return item.model_copy(update={"summary": extract_plain_text_summary(post.content_md)})
        return item

    def _build_detail_response(self, db_post: BlogPost, current_user: User) -> BlogPostDetailResponse:
        prev_post = (
            self._build_visible_query(current_user)
            .filter(
                or_(
                    BlogPost.created_at < db_post.created_at,
                    and_(
                        BlogPost.created_at == db_post.created_at,
                        BlogPost.id < db_post.id,
                    ),
                )
            )
            .order_by(BlogPost.created_at.desc(), BlogPost.id.desc())
            .first()
        )
        next_post = (
            self._build_visible_query(current_user)
            .filter(
                or_(
                    BlogPost.created_at > db_post.created_at,
                    and_(
                        BlogPost.created_at == db_post.created_at,
                        BlogPost.id > db_post.id,
                    ),
                )
            )
            .order_by(BlogPost.created_at.asc(), BlogPost.id.asc())
            .first()
        )
        response_data = BlogPostResponse.model_validate(db_post).model_dump()
        response_data["prev_post"] = (
            self._build_list_item(prev_post) if prev_post else None
        )
        response_data["next_post"] = (
            self._build_list_item(next_post) if next_post else None
        )
        return BlogPostDetailResponse.model_validate(response_data)

    def get_blog_post(self, post_id: int, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.id == post_id).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

        blog_post_crud.increment_view_count(self.db, post_id)
        self.db.refresh(db_post)

        return self._build_detail_response(db_post, current_user)

    def get_blog_post_by_slug(self, slug: str, current_user: User) -> BlogPostDetailResponse:
        query = self._build_visible_query(current_user)
        db_post = query.filter(BlogPost.slug == slug).first()
        if not db_post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文章不存在")

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
                ttl = settings.CACHE_BLOG_LIST_TTL // 2
            elif skip == 0 and limit == 6:
                ttl = settings.CACHE_BLOG_HOME_TTL
                is_hot_key = True
            else:
                ttl = settings.CACHE_BLOG_LIST_TTL

            cached = get_json_cache(cache_key, BlogPostListResponse)
            if cached is not None:
                return cached

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
            items=[self._build_list_item(post) for post in posts],
            total=total,
        )

        if should_cache and cache_key is not None and ttl is not None:
            if not is_hot_key or lock_acquired:
                set_json_cache(cache_key, result, ttl, tags=["blog_posts"])
            if lock_acquired:
                release_cache_lock(cache_key)

        return result
