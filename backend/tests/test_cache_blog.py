"""博客与分类缓存集成测试。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.permission_levels import PermissionLevel
from app.schemas.blog_post import BlogPostListResponse, BlogPostListItem
from app.schemas.blog_category import BlogCategoryWithPostCount
from app.services.blog_post_service import BlogPostService
from app.services.blog_category_service import BlogCategoryService
from app.services.comment_service import CommentService


def _make_mock_post():
    """构造可用于 BlogPostListItem.model_validate 的 mock post。"""
    post = MagicMock()
    post.id = 1
    post.user_id = 1
    post.title = "Test"
    post.slug = "test"
    post.summary = None
    post.cover_image_url = None
    post.category_id = 1
    post.category = MagicMock()
    post.category.id = 1
    post.category.name = "Cat"
    post.category.slug = "cat"
    post.tags = []
    post.status = "published"
    post.view_count = 0
    post.comment_count = 0
    post.created_at = datetime.now(timezone.utc)
    post.updated_at = datetime.now(timezone.utc)
    post.author = MagicMock()
    post.author.id = 1
    post.author.username = "user"
    post.author.avatar_url = None
    return post


class TestBlogPostListCache:
    """测试博客公共列表缓存。"""

    @patch("app.services.blog_post_service.acquire_cache_lock")
    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_first_call_queries_db_and_sets_cache(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
        mock_lock,
    ):
        """第一次请求未命中缓存，应查库并写入缓存。"""
        mock_get_cache.return_value = None
        mock_lock.return_value = True
        mock_get_posts.return_value = [_make_mock_post()]
        mock_count.return_value = 1

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.USER

        result = service.list_blog_posts(
            skip=0, limit=10, status=None, category_id=None,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )

        assert isinstance(result, BlogPostListResponse)
        assert result.total == 1
        mock_get_posts.assert_called_once()
        mock_set_cache.assert_called_once()
        mock_lock.assert_not_called()  # 非首页热门 key 不加锁

    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_second_call_hits_cache(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
    ):
        """第二次请求命中缓存，应直接返回，不走数据库。"""
        cached = BlogPostListResponse(items=[], total=0)
        mock_get_cache.return_value = cached

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.USER

        result = service.list_blog_posts(
            skip=0, limit=10, status=None, category_id=None,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )

        assert result is cached
        mock_get_posts.assert_not_called()
        mock_count.assert_not_called()
        mock_set_cache.assert_not_called()

    @patch("app.services.blog_post_service.release_cache_lock")
    @patch("app.services.blog_post_service.acquire_cache_lock")
    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_home_hot_key_acquires_lock(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
        mock_lock,
        mock_release,
    ):
        """首页热门 key（skip=0, limit=6）应尝试获取锁，抢到后写缓存并释放。"""
        mock_get_cache.return_value = None
        mock_lock.return_value = True
        mock_get_posts.return_value = [_make_mock_post()]
        mock_count.return_value = 1

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.USER

        result = service.list_blog_posts(
            skip=0, limit=6, status=None, category_id=None,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )

        assert isinstance(result, BlogPostListResponse)
        mock_lock.assert_called_once()
        mock_set_cache.assert_called_once()
        mock_release.assert_called_once()

    @patch("app.services.blog_post_service.release_cache_lock")
    @patch("app.services.blog_post_service.acquire_cache_lock")
    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_home_hot_key_miss_lock_skips_cache_write(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
        mock_lock,
        mock_release,
    ):
        """首页热门 key 未抢到锁时，应走数据库但不写缓存。"""
        mock_get_cache.return_value = None
        mock_lock.return_value = False
        mock_get_posts.return_value = [_make_mock_post()]
        mock_count.return_value = 1

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.USER

        result = service.list_blog_posts(
            skip=0, limit=6, status=None, category_id=None,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )

        assert isinstance(result, BlogPostListResponse)
        mock_lock.assert_called_once()
        mock_set_cache.assert_not_called()
        mock_release.assert_not_called()

    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_super_admin_include_unpublished_bypasses_cache(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
    ):
        """超管 include_unpublished=true 时不读写公共缓存。"""
        mock_get_posts.return_value = [_make_mock_post()]
        mock_count.return_value = 1

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        result = service.list_blog_posts(
            skip=0, limit=10, status="draft", category_id=None,
            tag=None, q=None, include_unpublished=True, current_user=current_user,
        )

        assert isinstance(result, BlogPostListResponse)
        mock_get_cache.assert_not_called()
        mock_set_cache.assert_not_called()

    @patch("app.services.blog_post_service.get_json_cache")
    @patch("app.services.blog_post_service.set_json_cache")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_posts_count")
    def test_different_params_generate_different_keys(
        self,
        mock_count,
        mock_get_posts,
        mock_set_cache,
        mock_get_cache,
    ):
        """不同查询参数应生成不同缓存 key。"""
        mock_get_cache.return_value = None
        mock_get_posts.return_value = [_make_mock_post()]
        mock_count.return_value = 1

        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.USER

        service.list_blog_posts(
            skip=0, limit=10, status=None, category_id=1,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )
        service.list_blog_posts(
            skip=0, limit=10, status=None, category_id=2,
            tag=None, q=None, include_unpublished=False, current_user=current_user,
        )

        # set_json_cache 被调用两次，key 不同
        assert mock_set_cache.call_count == 2
        key1 = mock_set_cache.call_args_list[0][0][0]
        key2 = mock_set_cache.call_args_list[1][0][0]
        assert key1 != key2


class TestBlogPostCacheInvalidation:
    """测试博客写操作后缓存失效。"""

    @pytest.mark.asyncio
    @patch("app.services.blog_post_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_post_service.BlogPostEmbeddingService")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_slug")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
    @patch("app.services.blog_post_service.blog_post_crud.create_blog_post")
    async def test_create_draft_post_does_not_invalidate_cache(
        self, mock_create, mock_get_by_id, mock_get_slug, mock_embed_cls, mock_invalidate
    ):
        """创建 draft 文章后不应触发缓存失效（草稿不影响公共列表）。"""
        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        post_in = MagicMock()
        post_in.slug = "test"
        post_in.content_md = "short content"
        post_in.model_copy.return_value = post_in
        post_in.model_dump.return_value = {"title": "t", "status": "draft"}

        mock_get_slug.return_value = None
        db_post = MagicMock()
        db_post.status = "draft"
        db_post.id = 1
        mock_create.return_value = db_post
        mock_get_by_id.return_value = db_post

        with patch("app.services.blog_post_service.upload_image") as mock_upload:
            mock_upload.return_value = "http://cover.jpg"
            await service.create_blog_post(post_in, current_user, MagicMock())

        mock_invalidate.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.blog_post_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_post_service.BlogPostEmbeddingService")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
    async def test_publish_post_invalidates_cache(
        self, mock_get_by_id, mock_embed_cls, mock_invalidate
    ):
        """发布文章后应失效缓存。"""
        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        db_post = MagicMock()
        db_post.status = "draft"
        db_post.id = 1
        mock_get_by_id.return_value = db_post

        await service.publish_blog_post(1, current_user)
        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.blog_post_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_post_service.BlogPostEmbeddingService")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
    async def test_unpublish_post_invalidates_cache(
        self, mock_get_by_id, mock_embed_cls, mock_invalidate
    ):
        """下线文章后应失效缓存。"""
        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        db_post = MagicMock()
        db_post.status = "published"
        db_post.id = 1
        mock_get_by_id.return_value = db_post

        await service.unpublish_blog_post(1, current_user)
        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.blog_post_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_post_service.BlogPostEmbeddingService")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
    @patch("app.services.blog_post_service.blog_post_crud.update_blog_post")
    async def test_update_post_invalidates_cache(
        self, mock_update, mock_get_by_id, mock_embed_cls, mock_invalidate
    ):
        """更新文章后应失效缓存。"""
        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        db_post = MagicMock()
        db_post.id = 1
        db_post.slug = "old"
        db_post.cover_image_url = None
        mock_get_by_id.return_value = db_post

        post_in = MagicMock()
        post_in.model_dump.return_value = {"title": "new"}
        mock_update.return_value = db_post

        await service.update_blog_post(1, post_in, current_user)
        mock_invalidate.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.blog_post_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_post_service.BlogPostEmbeddingService")
    @patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
    @patch("app.services.blog_post_service.blog_post_crud.hard_delete_blog_post")
    async def test_hard_delete_invalidates_cache(
        self, mock_delete, mock_get_by_id, mock_embed_cls, mock_invalidate
    ):
        """硬删除文章后应失效缓存。"""
        db = MagicMock()
        service = BlogPostService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        db_post = MagicMock()
        db_post.cover_image_url = None
        db_post.content_md = None
        mock_get_by_id.return_value = db_post
        mock_delete.return_value = 1

        await service.hard_delete_blog_post(1, current_user)
        mock_invalidate.assert_called_once()


class TestBlogCategoryListCache:
    """测试博客分类列表缓存。"""

    @patch("app.services.blog_category_service.BlogCategoryWithPostCount.model_validate")
    @patch("app.services.blog_category_service.get_json_cache")
    @patch("app.services.blog_category_service.set_json_cache")
    @patch("app.services.blog_category_service.blog_category_crud.get_all_categories")
    def test_first_call_queries_db_and_sets_cache(
        self, mock_get_all, mock_set_cache, mock_get_cache, mock_model_validate
    ):
        """第一次请求未命中缓存，应查库并写入缓存。"""
        mock_get_cache.return_value = None
        mock_model_validate.return_value = MagicMock()
        mock_get_all.return_value = [MagicMock()]

        db = MagicMock()
        db.query.return_value.group_by.return_value.all.return_value = []
        service = BlogCategoryService(db)

        result = service.list_categories()

        assert isinstance(result, list)
        mock_get_all.assert_called_once()
        mock_set_cache.assert_called_once()

    @patch("app.services.blog_category_service.get_json_cache")
    @patch("app.services.blog_category_service.set_json_cache")
    @patch("app.services.blog_category_service.blog_category_crud.get_all_categories")
    def test_second_call_hits_cache(
        self, mock_get_all, mock_set_cache, mock_get_cache
    ):
        """第二次请求命中缓存，应直接返回，不走数据库。"""
        cached = [BlogCategoryWithPostCount(id=1, name="Test", slug="test", post_count=0)]
        mock_get_cache.return_value = cached

        db = MagicMock()
        service = BlogCategoryService(db)

        result = service.list_categories()
        assert result is cached
        mock_get_all.assert_not_called()
        mock_set_cache.assert_not_called()


class TestBlogCategoryCacheInvalidation:
    """测试分类写操作后缓存失效。"""

    @patch("app.services.blog_category_service.BlogCacheInvalidator.invalidate_blog_categories")
    @patch("app.services.blog_category_service.blog_category_crud.create_category")
    @patch("app.services.blog_category_service.blog_category_crud.get_category_by_slug")
    def test_create_category_invalidates_cache(self, mock_get_slug, mock_create, mock_invalidate):
        db = MagicMock()
        service = BlogCategoryService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        mock_get_slug.return_value = None
        category_in = MagicMock()
        category_in.slug = "test"
        mock_create.return_value = MagicMock()

        service.create_category(category_in, current_user)
        mock_invalidate.assert_called_once()

    @patch("app.services.blog_category_service.BlogCacheInvalidator.invalidate_all")
    @patch("app.services.blog_category_service.blog_category_crud.update_category")
    @patch("app.services.blog_category_service.blog_category_crud.get_category_by_id")
    def test_update_category_invalidates_cache(self, mock_get, mock_update, mock_invalidate):
        db = MagicMock()
        service = BlogCategoryService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        mock_get.return_value = MagicMock()
        mock_get.return_value.slug = "old"
        mock_update.return_value = MagicMock()

        category_in = MagicMock()
        category_in.model_dump.return_value = {}

        service.update_category(1, category_in, current_user)
        mock_invalidate.assert_called_once()

    @patch("app.services.blog_category_service.BlogCacheInvalidator.invalidate_blog_categories")
    @patch("app.services.blog_category_service.blog_category_crud.delete_category")
    @patch("app.services.blog_category_service.blog_category_crud.get_category_by_id")
    @patch("app.services.blog_category_service.blog_category_crud.count_posts_in_category")
    def test_delete_category_invalidates_cache(self, mock_count, mock_get, mock_delete, mock_invalidate):
        db = MagicMock()
        service = BlogCategoryService(db)
        current_user = MagicMock()
        current_user.permission = PermissionLevel.SUPER_ADMIN

        mock_get.return_value = MagicMock()
        mock_count.return_value = 0
        mock_delete.return_value = 1

        service.delete_category(1, current_user)
        mock_invalidate.assert_called_once()


class TestCommentCacheInvalidation:
    """测试评论操作后博客缓存失效。"""

    @patch("app.services.comment_service.BlogCacheInvalidator.invalidate_blog_posts")
    @patch("app.services.comment_service.comment_crud.create_comment")
    @patch("app.services.comment_service.comment_crud.get_comment_by_id")
    @patch("app.services.comment_service.blog_post_crud.get_blog_post_by_id")
    def test_create_blog_comment_invalidates_blog_cache(
        self, mock_get_post, mock_get_comment, mock_create, mock_invalidate
    ):
        """创建博客评论后应失效博客文章缓存。"""
        db = MagicMock()
        service = CommentService(db)
        current_user = MagicMock()

        mock_post = MagicMock()
        mock_get_post.return_value = mock_post

        comment_in = MagicMock()
        comment_in.target_type = "blog_post"
        comment_in.target_id = 1
        comment_in.content = "test"
        comment_in.parent_id = None
        comment_in.is_nested = False
        comment_in.nested_parent_id = None
        comment_in.model_dump.return_value = {
            "target_type": "blog_post", "target_id": 1, "content": "test",
            "parent_id": None, "is_nested": False, "nested_parent_id": None,
        }

        db_comment = MagicMock()
        mock_create.return_value = db_comment
        mock_get_comment.return_value = db_comment

        service.create_comment(comment_in, current_user)
        mock_invalidate.assert_called_once()

    @patch("app.services.comment_service.BlogCacheInvalidator.invalidate_blog_posts")
    @patch("app.services.comment_service.comment_crud.create_comment")
    @patch("app.services.comment_service.comment_crud.get_comment_by_id")
    @patch("app.services.comment_service.forum_reply_crud.get_reply_by_id")
    def test_create_forum_comment_does_not_invalidate_blog_cache(
        self, mock_get_reply, mock_get_comment, mock_create, mock_invalidate
    ):
        """创建论坛评论后不应失效博客文章缓存。"""
        db = MagicMock()
        service = CommentService(db)
        current_user = MagicMock()

        mock_reply = MagicMock()
        mock_get_reply.return_value = mock_reply

        comment_in = MagicMock()
        comment_in.target_type = "forum_reply"
        comment_in.target_id = 1
        comment_in.content = "test"
        comment_in.parent_id = 1
        comment_in.is_nested = False
        comment_in.nested_parent_id = None
        comment_in.model_dump.return_value = {
            "target_type": "forum_reply", "target_id": 1, "content": "test",
            "parent_id": 1, "is_nested": False, "nested_parent_id": None,
        }

        db_comment = MagicMock()
        mock_create.return_value = db_comment
        mock_get_comment.return_value = db_comment

        service.create_comment(comment_in, current_user)
        mock_invalidate.assert_not_called()

    @patch("app.services.comment_service.BlogCacheInvalidator.invalidate_blog_posts")
    @patch("app.services.comment_service.comment_crud.delete_comment")
    @patch("app.services.comment_service.comment_crud.get_comment_by_id")
    def test_delete_blog_comment_invalidates_blog_cache(
        self, mock_get_comment, mock_delete, mock_invalidate
    ):
        """删除博客评论后应失效博客文章缓存。"""
        db = MagicMock()
        service = CommentService(db)
        current_user = MagicMock()
        current_user.id = 1

        db_comment = MagicMock()
        db_comment.user_id = 1
        db_comment.target_type = "blog_post"
        db_comment.parent_id = None
        mock_get_comment.return_value = db_comment

        service.delete_comment(1, current_user)
        mock_invalidate.assert_called_once()
