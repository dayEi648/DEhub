"""
测试从 Markdown 正文中提取 OSS 图片 URL 的能力
"""
import pytest
from unittest.mock import patch

from app.storage.oss import extract_oss_image_urls_from_markdown


class TestExtractOssImageUrlsFromMarkdown:
    """验证 Markdown 图片 URL 提取与 OSS 过滤逻辑"""

    @patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "my-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
    def test_extract_multiple_oss_urls(self):
        content = """
# 标题

![图1](https://cdn.example.com/uploads/images/20240101/abc.jpg)

一些文字

![图2](https://cdn.example.com/uploads/images/20240102/def.png)

![外部图](https://external.com/image.png)

![图3](https://oss-cn-beijing.aliyuncs.com/my-bucket/forum/posts/xyz.webp)
"""
        urls = extract_oss_image_urls_from_markdown(content)
        assert len(urls) == 3
        assert urls[0] == "https://cdn.example.com/uploads/images/20240101/abc.jpg"
        assert urls[1] == "https://cdn.example.com/uploads/images/20240102/def.png"
        assert urls[2] == "https://oss-cn-beijing.aliyuncs.com/my-bucket/forum/posts/xyz.webp"

    @patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "my-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
    def test_filter_out_external_urls(self):
        content = """
![外部1](https://imgur.com/abc.png)
![外部2](https://github.com/user/repo/assets/123.jpg)
"""
        urls = extract_oss_image_urls_from_markdown(content)
        assert urls == []

    @patch("app.storage.oss.settings.OSS_DOMAIN", "")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "dehub-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    def test_without_custom_domain(self):
        content = """
![图](https://oss-cn-hangzhou.aliyuncs.com/dehub-bucket/blog/covers/test.jpg)
![外部](https://other.com/pic.png)
"""
        urls = extract_oss_image_urls_from_markdown(content)
        assert len(urls) == 1
        assert urls[0] == "https://oss-cn-hangzhou.aliyuncs.com/dehub-bucket/blog/covers/test.jpg"

    @patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "my-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
    def test_deduplication(self):
        content = """
![图1](https://cdn.example.com/uploads/images/20240101/abc.jpg)
![图1重复](https://cdn.example.com/uploads/images/20240101/abc.jpg)
"""
        urls = extract_oss_image_urls_from_markdown(content)
        assert len(urls) == 1

    @patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "my-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
    def test_empty_and_no_images(self):
        assert extract_oss_image_urls_from_markdown("") == []
        assert extract_oss_image_urls_from_markdown("纯文本没有图片") == []
        assert extract_oss_image_urls_from_markdown("# 标题\n\n段落") == []

    @patch("app.storage.oss.settings.OSS_DOMAIN", "https://cdn.example.com")
    @patch("app.storage.oss.settings.OSS_BUCKET_NAME", "my-bucket")
    @patch("app.storage.oss.settings.OSS_ENDPOINT", "oss-cn-beijing.aliyuncs.com")
    def test_mixed_markdown_elements(self):
        content = """
# 标题
[链接](https://cdn.example.com/not-an-image.jpg)
![图片](https://cdn.example.com/uploads/images/20240101/abc.jpg)
`代码块`
"""
        urls = extract_oss_image_urls_from_markdown(content)
        assert len(urls) == 1
        assert urls[0] == "https://cdn.example.com/uploads/images/20240101/abc.jpg"
