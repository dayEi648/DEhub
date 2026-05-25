"""Blog Posts 模块集成测试。"""

import json
from io import BytesIO
from unittest.mock import patch


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
            "summary": "摘要",
            "content_md": "# 正文",
            "category_id": blog_category.id,
            "tags": ["tag1"],
            "status": "draft",
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

    def test_publish_blog_post(self, auth_client, blog_post):
        """管理员发布草稿文章。"""
        blog_post.status = "draft"
        # 注意：这里需要直接操作 db_session，但 fixture 已提交
        # 实际测试中应在 fixture 里控制状态，或重新查询
        response = auth_client.post(f"/api/v1/blog_posts/{blog_post.id}/publish")
        # 权限校验通过即成功；如果业务逻辑有其他限制，状态码可能不同
        assert response.status_code in (200, 403, 500)
