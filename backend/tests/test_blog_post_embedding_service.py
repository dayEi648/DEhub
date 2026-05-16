"""blog_post_embedding_service 单元测试。"""

from unittest.mock import MagicMock

from app.services.blog_post_embedding_service import BlogPostEmbeddingService


class TestBuildEmbeddingText:
    """测试 _build_embedding_text 的截断逻辑。"""

    def test_truncation_respects_sentence_boundary(self):
        """超长文本应截断到最近的句子边界，避免语义断裂。"""
        post = MagicMock()
        post.title = "测试标题"
        post.summary = "测试摘要。"
        post.tags = ["tag1", "tag2"]
        # 构造一个超长的正文，包含多个句子
        post.content_md = "这是第一句。这是第二句。这是第三句。" + "x" * 10000

        text = BlogPostEmbeddingService._build_embedding_text(post)
        assert len(text) <= 6000
        # 最后一个字符应该是句子结束符
        assert text[-1] in {"。", ".", "\n"}

    def test_no_truncation_when_short(self):
        """短文本不应被截断。"""
        post = MagicMock()
        post.title = "短标题"
        post.summary = None
        post.tags = None
        post.content_md = "短内容。"

        text = BlogPostEmbeddingService._build_embedding_text(post)
        assert "短标题" in text
        assert "短内容。" in text
