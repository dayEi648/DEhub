"""blog_post_embedding_service 搜索相关单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.blog_post_embedding_service import BlogPostEmbeddingService


class TestBlogPostEmbeddingSearch:
    """测试 blog_post_embedding_search 核心逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = BlogPostEmbeddingService(self.mock_db)

    def test_returns_empty_for_blank_query(self):
        """空字符串或仅空白字符的 query 应返回空列表。"""
        assert self.service.blog_post_embedding_search("") == []
        assert self.service.blog_post_embedding_search("   ") == []

    @patch("app.services.blog_post_embedding_service.get_embedding_client")
    def test_returns_empty_when_embedding_fails(self, mock_get_embed):
        """embed_query 抛出异常时应返回空列表，不向上抛。"""
        mock_client = MagicMock()
        mock_client.embed_query.side_effect = RuntimeError("API 超时")
        mock_get_embed.return_value = mock_client

        result = self.service.blog_post_embedding_search("测试查询")
        assert result == []

    @patch("app.services.blog_post_embedding_service.get_embedding_client")
    @patch("app.services.blog_post_embedding_service.embed_crud.search_similar")
    def test_filters_by_similarity_threshold(self, mock_search, mock_get_embed):
        """相似度低于阈值的结果应被过滤。"""
        # mock embedding client
        mock_client = MagicMock()
        mock_client.embed_query.return_value = [0.1] * 1024
        mock_get_embed.return_value = mock_client

        # mock raw results: (embedding_record, distance)
        # distance 0.2 -> similarity 0.8 (通过)
        # distance 0.5 -> similarity 0.5 (被过滤，因为阈值 0.6)
        # distance 0.1 -> similarity 0.9 (通过)
        mock_record1 = MagicMock(post_id=1)
        mock_record2 = MagicMock(post_id=2)
        mock_record3 = MagicMock(post_id=3)
        mock_search.return_value = [
            (mock_record1, 0.2),
            (mock_record2, 0.5),
            (mock_record3, 0.1),
        ]

        # mock BlogPost query
        mock_post1 = MagicMock()
        mock_post1.id = 1
        mock_post1.title = "文章1"
        mock_post1.slug = "post-1"
        mock_post1.summary = "摘要1"
        mock_post1.category = MagicMock()
        mock_post1.category.name = "分类1"

        mock_post3 = MagicMock()
        mock_post3.id = 3
        mock_post3.title = "文章3"
        mock_post3.slug = "post-3"
        mock_post3.summary = "摘要3"
        mock_post3.category = MagicMock()
        mock_post3.category.name = "分类3"

        self.mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            mock_post1,
            mock_post3,
        ]

        result = self.service.blog_post_embedding_search(
            "查询", top_k=5, min_similarity=0.6
        )

        # 只返回相似度 >= 0.6 的结果
        assert len(result) == 2
        assert result[0].post_id == 1
        assert result[1].post_id == 3
