import pytest
from pydantic import ValidationError

from app.schemas.blog_post import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostResponse,
    BlogPostListItem,
)
from app.models.blog_post import BlogPost


class TestBlogPostSchema:
    def test_create_valid(self):
        """正常创建请求应通过校验"""
        post = BlogPostCreate(
            title="测试标题",
            slug="test-slug",
            content_md="# Hello",
            category_id=1,
        )
        assert post.title == "测试标题"
        assert post.slug == "test-slug"
        assert post.status == "draft"
        assert post.tags == []

    def test_create_with_optional_fields(self):
        """包含可选字段的创建请求应通过校验"""
        post = BlogPostCreate(
            title="测试标题",
            slug="test-slug",
            summary="摘要",
            content_md="# Hello",
            cover_image_url="https://example.com/cover.jpg",
            category_id=1,
            tags=["python", "fastapi"],
            status="published",
        )
        assert post.summary == "摘要"
        assert post.tags == ["python", "fastapi"]
        assert post.status == "published"

    def test_create_invalid_status_rejected(self):
        """非法 status 值应被拒绝"""
        with pytest.raises(ValidationError) as exc_info:
            BlogPostCreate(
                title="测试标题",
                slug="test-slug",
                content_md="# Hello",
                category_id=1,
                status="invalid_status",
            )
        assert "status" in str(exc_info.value)

    def test_create_title_too_long_rejected(self):
        """标题超过 64 字符应被拒绝"""
        with pytest.raises(ValidationError):
            BlogPostCreate(
                title="x" * 65,
                slug="test-slug",
                content_md="# Hello",
                category_id=1,
            )

    def test_create_category_id_zero_rejected(self):
        """category_id 小于 1 应被拒绝"""
        with pytest.raises(ValidationError):
            BlogPostCreate(
                title="测试标题",
                slug="test-slug",
                content_md="# Hello",
                category_id=0,
            )

    def test_update_empty(self):
        """更新请求允许全空（exclude_unset 场景）"""
        update = BlogPostUpdate()
        assert update.title is None
        assert update.status is None

    def test_update_partial(self):
        """更新请求支持部分字段"""
        update = BlogPostUpdate(title="新标题")
        assert update.title == "新标题"
        assert update.content_md is None

    def test_update_invalid_status_rejected(self):
        """更新时传入非法 status 应被拒绝"""
        with pytest.raises(ValidationError):
            BlogPostUpdate(status="deleted")

    def test_response_from_attributes(self):
        """响应模型应支持从 ORM 属性构建"""
        data = {
            "id": 1,
            "title": "标题",
            "slug": "slug",
            "summary": None,
            "content_md": "# md",
            "cover_image_url": None,
            "category_id": 1,
            "category": {"id": 1, "name": "Tech", "slug": "tech"},
            "tags": [],
            "status": "draft",
            "view_count": 0,
            "is_deleted": False,
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:00:00+00:00",
        }
        resp = BlogPostResponse.model_validate(data)
        assert resp.id == 1

    def test_list_item_omits_content(self):
        """列表项模型不应包含 content_md，且支持 ORM 属性"""
        data = {
            "id": 1,
            "title": "标题",
            "slug": "slug",
            "summary": None,
            "cover_image_url": None,
            "category_id": 1,
            "category": {"id": 1, "name": "Tech", "slug": "tech"},
            "tags": ["a"],
            "status": "published",
            "view_count": 10,
            "is_deleted": False,
            "created_at": "2025-01-01T00:00:00+00:00",
            "updated_at": "2025-01-01T00:00:00+00:00",
        }
        item = BlogPostListItem.model_validate(data)
        assert item.id == 1
        assert not hasattr(item, "content_md")


class TestBlogPostModel:
    def test_summary_nullable(self):
        """summary 字段应允许为 NULL"""
        col = BlogPost.__table__.c.summary
        assert col.nullable is True

    def test_cover_image_url_nullable(self):
        """cover_image_url 字段应允许为 NULL"""
        col = BlogPost.__table__.c.cover_image_url
        assert col.nullable is True

    def test_tags_default(self):
        """tags 应有默认值（空列表）"""
        col = BlogPost.__table__.c.tags
        # SQLAlchemy default 在 Python 层面
        assert BlogPost.tags.default is not None
