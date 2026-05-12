import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.blog_category_service import BlogCategoryService
from app.schemas.blog_category import BlogCategoryCreate, BlogCategoryUpdate


class TestBlogCategoryServicePermission:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return BlogCategoryService(db)

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
        service._require_super_admin(super_admin)

    def test_require_super_admin_fail(self, service, normal_user):
        with pytest.raises(HTTPException) as exc_info:
            service._require_super_admin(normal_user)
        assert exc_info.value.status_code == 403

    def test_create_by_normal_user(self, service, normal_user):
        with pytest.raises(HTTPException) as exc_info:
            service.create_category(
                BlogCategoryCreate(name="Tech", slug="tech"), normal_user
            )
        assert exc_info.value.status_code == 403

    def test_slug_unique(self, service, super_admin):
        existing = MagicMock()
        existing.id = 1
        with patch(
            "app.services.blog_category_service.blog_category_crud.get_category_by_slug",
            return_value=existing,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service._ensure_slug_unique("duplicate-slug")
            assert exc_info.value.status_code == 400
            assert "slug 已存在" in exc_info.value.detail

    def test_delete_with_posts_blocked(self, db, service, super_admin):
        """删除有文章的分类应被阻止"""
        category = MagicMock()
        category.id = 1
        with patch(
            "app.services.blog_category_service.blog_category_crud.get_category_by_id",
            return_value=category,
        ):
            with patch(
                "app.services.blog_category_service.blog_category_crud.count_posts_in_category",
                return_value=3,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    service.delete_category(1, super_admin)
                assert exc_info.value.status_code == 400
                assert "该分类下还有文章" in exc_info.value.detail

    def test_delete_empty_category_allowed(self, db, service, super_admin):
        """删除无文章的分类应通过"""
        category = MagicMock()
        category.id = 1
        with patch(
            "app.services.blog_category_service.blog_category_crud.get_category_by_id",
            return_value=category,
        ):
            with patch(
                "app.services.blog_category_service.blog_category_crud.count_posts_in_category",
                return_value=0,
            ):
                with patch(
                    "app.services.blog_category_service.blog_category_crud.delete_category",
                    return_value=1,
                ):
                    service.delete_category(1, super_admin)


class TestBlogCategorySchema:
    def test_create_valid(self):
        cat = BlogCategoryCreate(name="技术", slug="tech", description="技术相关")
        assert cat.name == "技术"
        assert cat.slug == "tech"

    def test_create_name_too_long(self):
        with pytest.raises(Exception):
            BlogCategoryCreate(name="x" * 65, slug="tech")

    def test_update_empty(self):
        update = BlogCategoryUpdate()
        assert update.name is None
        assert update.slug is None

    def test_update_partial(self):
        update = BlogCategoryUpdate(name="新技术")
        assert update.name == "新技术"
        assert update.slug is None
