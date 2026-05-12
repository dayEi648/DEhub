import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.blog_post_service import BlogPostService
from app.models.blog_post import BlogPost
from app.schemas.blog_post import BlogPostCreate, BlogPostUpdate


class TestBlogPostServicePermission:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return BlogPostService(db)

    @pytest.fixture
    def super_admin(self):
        user = MagicMock()
        user.permission = 2
        return user

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.permission = 0
        return user

    def test_require_super_admin_pass(self, service, super_admin):
        """超管应通过权限校验"""
        service._require_super_admin(super_admin)

    def test_require_super_admin_fail(self, service, normal_user):
        """非超管应被 403 拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            service._require_super_admin(normal_user)
        assert exc_info.value.status_code == 403
        assert "超级管理员" in exc_info.value.detail

    def test_create_post_by_normal_user(self, db, service, normal_user):
        """普通用户创建文章应 403"""
        post_in = BlogPostCreate(
            title="标题", slug="slug", content_md="# md", category_id=1
        )
        with pytest.raises(HTTPException) as exc_info:
            service.create_blog_post(post_in, normal_user)
        assert exc_info.value.status_code == 403

    def test_slug_unique_check(self, db, service, super_admin):
        """重复 slug 应 400"""
        existing = MagicMock()
        existing.id = 1
        with patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_slug", return_value=existing):
            with pytest.raises(HTTPException) as exc_info:
                service._ensure_slug_unique("duplicate-slug")
            assert exc_info.value.status_code == 400
            assert "slug 已存在" in exc_info.value.detail

    def test_slug_unique_excluded_id(self, db, service, super_admin):
        """更新自身时排除自身 ID 应通过"""
        existing = MagicMock()
        existing.id = 1
        with patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_slug", return_value=existing):
            # 排除自身 ID，不应抛异常
            service._ensure_slug_unique("same-slug", exclude_post_id=1)


class TestBlogPostServiceReadPermission:
    @pytest.fixture
    def db(self):
        mock_db = MagicMock()
        mock_db.query.return_value = mock_db
        mock_db.filter.return_value = mock_db
        mock_db.order_by.return_value = mock_db
        mock_db.first.return_value = None
        return mock_db

    @pytest.fixture
    def service(self, db):
        return BlogPostService(db)

    @pytest.fixture
    def super_admin(self):
        user = MagicMock()
        user.permission = 2
        return user

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.permission = 0
        return user

    @pytest.fixture
    def published_post(self):
        post = MagicMock()
        post.id = 1
        post.title = "Published Post"
        post.slug = "published-post"
        post.summary = "Summary"
        post.content_md = "# Content"
        post.cover_image_url = None
        post.category_id = 1
        post.tags = []
        post.status = "published"
        post.is_deleted = False
        post.view_count = 0
        post.created_at = "2025-01-15T00:00:00+00:00"
        post.updated_at = "2025-01-15T00:00:00+00:00"
        return post

    @pytest.fixture
    def draft_post(self):
        post = MagicMock()
        post.id = 2
        post.title = "Draft Post"
        post.slug = "draft-post"
        post.summary = None
        post.content_md = "# Draft"
        post.cover_image_url = None
        post.category_id = 1
        post.tags = []
        post.status = "draft"
        post.is_deleted = False
        post.view_count = 0
        post.created_at = "2025-01-10T00:00:00+00:00"
        post.updated_at = "2025-01-10T00:00:00+00:00"
        return post

    def test_normal_user_can_view_published(self, db, service, normal_user, published_post):
        """普通用户可查看已发布文章"""
        db.first.return_value = published_post
        with patch("app.services.blog_post_service.blog_post_crud.increment_view_count"):
            result = service.get_blog_post(1, normal_user)
        assert result is not None

    def test_normal_user_cannot_view_draft(self, db, service, normal_user, draft_post):
        """普通用户查看草稿应 404"""
        db.first.return_value = None  # 查询被权限过滤掉了
        with pytest.raises(HTTPException) as exc_info:
            service.get_blog_post(2, normal_user)
        assert exc_info.value.status_code == 404

    def test_super_admin_can_view_draft(self, db, service, super_admin, draft_post):
        """超管可查看草稿"""
        db.first.return_value = draft_post
        with patch("app.services.blog_post_service.blog_post_crud.increment_view_count"):
            result = service.get_blog_post(2, super_admin)
        assert result is not None

    def test_list_posts_normal_user_forces_published(self, db, service, normal_user):
        """普通用户列表强制只看 published"""
        with patch("app.services.blog_post_service.blog_post_crud.get_blog_posts") as mock_get:
            mock_get.return_value = []
            service.list_blog_posts(
                skip=0, limit=20, status="draft", category_id=None,
                tag=None, q=None, include_unpublished=True, current_user=normal_user
            )
            call_args = mock_get.call_args.kwargs
            assert call_args["status"] == "published"

    def test_list_posts_super_admin_can_include_unpublished(self, db, service, super_admin):
        """超管可查询未发布"""
        with patch("app.services.blog_post_service.blog_post_crud.get_blog_posts") as mock_get:
            mock_get.return_value = []
            service.list_blog_posts(
                skip=0, limit=20, status="draft", category_id=None,
                tag=None, q=None, include_unpublished=True, current_user=super_admin
            )
            call_args = mock_get.call_args.kwargs
            assert call_args["status"] == "draft"


class TestBlogPostServiceCleanup:
    def test_cleanup_deleted_posts(self):
        """一键清理应删除所有 is_deleted=True 的文章"""
        db = MagicMock()
        service = BlogPostService(db)
        super_admin = MagicMock()
        super_admin.permission = 2

        db.query.return_value.filter.return_value.delete.return_value = 5

        count = service.cleanup_deleted_posts(super_admin)
        assert count == 5
        db.commit.assert_called_once()
