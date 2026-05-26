"""Blog Posts 模块集成测试。"""

import json
from io import BytesIO
from unittest.mock import AsyncMock, patch


class TestBlogPostListAndDetail:
    def test_list_blog_posts(self, auth_client, blog_post):
        """列表接口应返回文章列表。"""
        response = auth_client.get("/api/v1/blog_posts/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        slugs = [p["slug"] for p in data["items"]]
        assert blog_post.slug in slugs

    def test_get_blog_post_detail(self, auth_client, blog_post):
        """详情接口应返回文章内容。"""
        response = auth_client.get(f"/api/v1/blog_posts/{blog_post.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == blog_post.title
        assert data["slug"] == blog_post.slug

    def test_get_blog_post_by_slug(self, auth_client, blog_post):
        """通过 slug 获取详情应成功。"""
        response = auth_client.get(f"/api/v1/blog_posts/by-slug/{blog_post.slug}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == blog_post.id


class TestBlogPostAdminOperations:
    @patch("app.services.blog_post_service.upload_image")
    def test_create_blog_post(self, mock_upload_image, auth_client, blog_category):
        """管理员创建文章应返回 201。"""
        mock_upload_image.return_value = "https://oss.example.com/covers/test.jpg"
        post_in = {
            "title": "新建文章",
            "slug": "new-post",
            "content_md": "# 正文",
            "category_id": blog_category.id,
            "tags": ["tag1"],
        }
        file_data = {"file": ("cover.png", BytesIO(b"fake-image"), "image/png")}
        response = auth_client.post(
            "/api/v1/blog_posts/",
            data={"post_in": json.dumps(post_in)},
            files=file_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "新建文章"
        assert data["cover_image_url"] == "https://oss.example.com/covers/test.jpg"

    def test_publish_blog_post(self, auth_client, draft_blog_post):
        """管理员发布草稿文章应成功，并变为 published 状态。"""
        response = auth_client.post(f"/api/v1/blog_posts/{draft_blog_post.id}/publish")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"

    def test_publish_already_published_post(self, auth_client, blog_post):
        """发布已经是 published 状态的文章应返回 400。"""
        response = auth_client.post(f"/api/v1/blog_posts/{blog_post.id}/publish")
        assert response.status_code == 400
        assert "已是发布状态" in response.json()["message"]

    @patch("app.services.blog_post_service.upload_image")
    @patch("app.services.blog_post_service.BlogPostService._auto_generate_summary", new_callable=AsyncMock)
    def test_create_long_blog_post_generates_summary(
        self, mock_generate_summary, mock_upload_image, auth_client, blog_category
    ):
        """创建正文字数超过 2000 的文章时应自动生成摘要。"""
        mock_upload_image.return_value = "https://oss.example.com/covers/test.jpg"
        mock_generate_summary.return_value = "这是一篇长文自动生成的摘要。"

        long_content = "这是一段正文内容。" * 250  # 确保超过 2000 字
        post_in = {
            "title": "长文测试",
            "slug": "long-post",
            "content_md": long_content,
            "category_id": blog_category.id,
            "tags": ["long"],
        }
        file_data = {"file": ("cover.png", BytesIO(b"fake-image"), "image/png")}
        response = auth_client.post(
            "/api/v1/blog_posts/",
            data={"post_in": json.dumps(post_in)},
            files=file_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"
        assert data["summary"] == "这是一篇长文自动生成的摘要。"
        mock_generate_summary.assert_awaited_once()

    @patch("app.services.blog_post_service.upload_image")
    @patch("app.services.blog_post_service.BlogPostService._auto_generate_summary", new_callable=AsyncMock)
    def test_update_blog_post_content_regenerates_summary(
        self, mock_generate_summary, mock_upload_image, auth_client, blog_post
    ):
        """更新已发布文章的正文时，应重新生成摘要并同步向量。"""
        mock_upload_image.return_value = "https://oss.example.com/covers/new.jpg"
        mock_generate_summary.return_value = "更新后的摘要。"

        long_content = "这是更新后的正文内容。" * 250
        post_in = {
            "title": blog_post.title,
            "slug": blog_post.slug,
            "content_md": long_content,
            "category_id": blog_post.category_id,
            "tags": blog_post.tags,
        }
        response = auth_client.put(
            f"/api/v1/blog_posts/{blog_post.id}",
            data={"post_in": json.dumps(post_in)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "更新后的摘要。"
        mock_generate_summary.assert_awaited_once()

    @patch("app.services.blog_post_service.upload_image")
    def test_update_blog_post_same_content_does_not_regenerate_summary(
        self, mock_upload_image, auth_client, blog_post
    ):
        """更新文章但不改变正文时，不应重新生成摘要。"""
        mock_upload_image.return_value = "https://oss.example.com/covers/new.jpg"

        # 只更新标题，不传 content_md
        post_in = {
            "title": "新标题",
        }
        response = auth_client.put(
            f"/api/v1/blog_posts/{blog_post.id}",
            data={"post_in": json.dumps(post_in)},
        )

        assert response.status_code == 200
        data = response.json()
        # 摘要应保持不变
        assert data["summary"] == blog_post.summary
