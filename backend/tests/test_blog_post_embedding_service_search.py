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

    @patch("app.services.blog_post_embedding_service.get_embedding_client")
    @patch("app.services.blog_post_embedding_service.embed_crud.search_similar")
    @patch("app.crud.blog_category.get_category_by_slug")
    def test_filters_by_category_slug(self, mock_get_cat, mock_search, mock_get_embed):
        """传入 category_slug 时应解析为 category_id 并传给 search_similar。"""
        mock_client = MagicMock()
        mock_client.embed_query.return_value = [0.1] * 1024
        mock_get_embed.return_value = mock_client

        mock_category = MagicMock()
        mock_category.id = 42
        mock_get_cat.return_value = mock_category

        mock_record = MagicMock(post_id=1)
        mock_search.return_value = [(mock_record, 0.1)]

        mock_post = MagicMock()
        mock_post.id = 1
        mock_post.title = "Docker 入门"
        mock_post.slug = "docker-intro"
        mock_post.summary = "摘要"
        mock_post.category = MagicMock()
        mock_post.category.name = "技术随笔"

        self.mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            mock_post
        ]

        result = self.service.blog_post_embedding_search(
            "Docker", top_k=5, category_slug="技术随笔"
        )

        assert len(result) == 1
        mock_get_cat.assert_called_once_with(self.mock_db, "技术随笔")
        mock_search.assert_called_once_with(
            self.mock_db, [0.1] * 1024, top_k=5, category_id=42
        )


class TestBlogPostEmbeddingSearchMultiQuery:
    """测试 blog_post_embedding_search_multi_query 多查询检索逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        self.service = BlogPostEmbeddingService(self.mock_db)

    @pytest.mark.asyncio
    @patch("app.services.blog_post_embedding_service.get_embedding_client")
    @patch("app.services.blog_post_embedding_service.embed_crud.search_similar")
    @patch("app.services.blog_post_embedding_service.RAGQueryService.expand_queries")
    async def test_multi_query_merges_and_reranks(self, mock_expand, mock_search, mock_get_embed):
        """多查询结果应合并去重并按相似度重排序。"""
        mock_client = MagicMock()
        mock_client.embed_query.return_value = [0.1] * 1024
        mock_get_embed.return_value = mock_client

        # 模拟改写返回3条query
        mock_expand.return_value = ["Docker", "容器化", "Docker 部署"]

        # 查询1返回 post_id=1(similarity=0.8), post_id=2(similarity=0.7)
        # 查询2返回 post_id=2(similarity=0.75), post_id=3(similarity=0.9)
        # 查询3返回 post_id=1(similarity=0.85)
        mock_record1 = MagicMock(post_id=1)
        mock_record2 = MagicMock(post_id=2)
        mock_record3 = MagicMock(post_id=3)

        def search_side_effect(db, embedding, top_k, category_id=None):
            call_index = mock_search.call_count - 1
            if call_index == 0:
                return [(mock_record1, 0.2), (mock_record2, 0.3)]
            if call_index == 1:
                return [(mock_record2, 0.25), (mock_record3, 0.1)]
            return [(mock_record1, 0.15)]

        mock_search.side_effect = search_side_effect

        mock_post1 = MagicMock()
        mock_post1.id = 1
        mock_post1.title = "Docker 基础"
        mock_post1.slug = "docker-base"
        mock_post1.summary = "摘要1"
        mock_post1.category = MagicMock()
        mock_post1.category.name = "技术随笔"

        mock_post2 = MagicMock()
        mock_post2.id = 2
        mock_post2.title = "Docker 进阶"
        mock_post2.slug = "docker-adv"
        mock_post2.summary = "摘要2"
        mock_post2.category = MagicMock()
        mock_post2.category.name = "技术随笔"

        mock_post3 = MagicMock()
        mock_post3.id = 3
        mock_post3.title = "Kubernetes 入门"
        mock_post3.slug = "k8s-intro"
        mock_post3.summary = "摘要3"
        mock_post3.category = MagicMock()
        mock_post3.category.name = "技术随笔"

        self.mock_db.query.return_value.options.return_value.filter.return_value.all.return_value = [
            mock_post1, mock_post2, mock_post3
        ]

        with patch(
            "app.services.blog_post_embedding_service.settings.RAG_MIN_SIMILARITY",
            0.0,
        ), patch(
            "app.services.blog_post_embedding_service.settings.RAG_BLOG_TOP_K",
            2,
        ), patch(
            "app.services.blog_post_embedding_service.settings.RAG_MULTI_QUERY_TOP_K_PER_QUERY",
            5,
        ):
            result = await self.service.blog_post_embedding_search_multi_query(
                "Docker", top_k=2
            )

        # 合并后去重：post1 最高 0.85, post3 最高 0.9, post2 最高 0.75
        # 重排序后取前2：post3(0.9), post1(0.85)
        assert len(result) == 2
        assert result[0].post_id == 3  # 最高相似度
        assert result[1].post_id == 1

    @pytest.mark.asyncio
    @patch("app.services.blog_post_embedding_service.RAGQueryService.expand_queries")
    async def test_multi_query_disabled_fallback_to_single(self, mock_expand):
        """改写被禁用（返回单条且等于原query）时应降级走单查询。"""
        mock_expand.return_value = ["Docker"]

        with patch.object(
            self.service, "blog_post_embedding_search", return_value=[]
        ) as mock_single:
            result = await self.service.blog_post_embedding_search_multi_query("Docker")

        mock_single.assert_called_once()
        assert result == []


class TestMergeAndRerank:
    """测试 _merge_and_rerank 静态方法。"""

    def test_deduplicates_by_post_id_keeps_highest_score(self):
        """同一文章出现多次时保留最高相似度。"""
        from app.schemas.blog_post_embedding import BlogPostSearchResult

        r1 = BlogPostSearchResult(post_id=1, title="A", slug="a", summary=None, category_name="", similarity_score=0.8)
        r2 = BlogPostSearchResult(post_id=1, title="A", slug="a", summary=None, category_name="", similarity_score=0.9)
        r3 = BlogPostSearchResult(post_id=2, title="B", slug="b", summary=None, category_name="", similarity_score=0.7)

        merged = BlogPostEmbeddingService._merge_and_rerank([[r1, r3], [r2]], top_k=5)
        assert len(merged) == 2
        assert merged[0].post_id == 1
        assert merged[0].similarity_score == 0.9
        assert merged[1].post_id == 2

    def test_reranks_by_score_descending(self):
        """结果应按相似度降序排列。"""
        from app.schemas.blog_post_embedding import BlogPostSearchResult

        r1 = BlogPostSearchResult(post_id=1, title="A", slug="a", summary=None, category_name="", similarity_score=0.5)
        r2 = BlogPostSearchResult(post_id=2, title="B", slug="b", summary=None, category_name="", similarity_score=0.9)
        r3 = BlogPostSearchResult(post_id=3, title="C", slug="c", summary=None, category_name="", similarity_score=0.7)

        merged = BlogPostEmbeddingService._merge_and_rerank([[r1, r2], [r3]], top_k=5)
        scores = [r.similarity_score for r in merged]
        assert scores == [0.9, 0.7, 0.5]

    def test_respects_top_k(self):
        """应只返回 top_k 条。"""
        from app.schemas.blog_post_embedding import BlogPostSearchResult

        results = [
            BlogPostSearchResult(post_id=i, title=f"T{i}", slug=f"s{i}", summary=None, category_name="", similarity_score=0.9 - i * 0.1)
            for i in range(1, 6)
        ]

        merged = BlogPostEmbeddingService._merge_and_rerank([results], top_k=3)
        assert len(merged) == 3
        assert merged[0].post_id == 1
        assert merged[2].post_id == 3

    def test_empty_input_returns_empty(self):
        """空输入返回空列表。"""
        merged = BlogPostEmbeddingService._merge_and_rerank([], top_k=5)
        assert merged == []

        merged = BlogPostEmbeddingService._merge_and_rerank([[]], top_k=5)
        assert merged == []
