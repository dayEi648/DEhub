import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.blog_category import BlogCategory
from app.models.blog_post import BlogPost
from app.services.vector_sync_service import (
    _build_embedding_text,
    _compute_content_hash,
    sync_blog_post_embedding,
    sync_cleanup_orphaned_embeddings,
)


class TestBuildEmbeddingText:
    """测试嵌入文本组装逻辑"""

    def _make_post(
        self,
        title="测试标题",
        category_name="测试分类",
        tags=None,
        summary=None,
        content_md="正文内容",
    ):
        post = MagicMock(spec=BlogPost)
        post.title = title
        post.category = MagicMock(spec=BlogCategory)
        post.category.name = category_name
        post.tags = tags or []
        post.summary = summary
        post.content_md = content_md
        return post

    def test_full_fields(self):
        """所有字段齐全时应完整组装"""
        post = self._make_post(
            title="Hello",
            category_name="Python",
            tags=["fastapi", "sqlalchemy"],
            summary="这是摘要",
            content_md="# Hello World",
        )
        text = _build_embedding_text(post)
        assert "标题: Hello" in text
        assert "分类: Python" in text
        assert "标签: fastapi, sqlalchemy" in text
        assert "摘要: 这是摘要" in text
        assert "正文: # Hello World" in text

    def test_empty_category(self):
        """分类名称为空时不应输出分类行"""
        post = self._make_post(category_name="")
        text = _build_embedding_text(post)
        assert "分类:" not in text

    def test_none_category(self):
        """分类为 None 时不应输出分类行"""
        post = self._make_post()
        post.category = None
        text = _build_embedding_text(post)
        assert "分类:" not in text

    def test_empty_tags(self):
        """标签为空列表时不应输出行"""
        post = self._make_post(tags=[])
        text = _build_embedding_text(post)
        assert "标签:" not in text

    def test_none_summary(self):
        """摘要为 None 时不应输出行"""
        post = self._make_post(summary=None)
        text = _build_embedding_text(post)
        assert "摘要:" not in text


class TestComputeContentHash:
    """测试内容指纹计算"""

    def test_same_text_same_hash(self):
        """相同文本应产生相同哈希"""
        text = "hello world"
        assert _compute_content_hash(text) == _compute_content_hash(text)

    def test_different_text_different_hash(self):
        """不同文本应产生不同哈希"""
        assert _compute_content_hash("a") != _compute_content_hash("b")

    def test_utf8_text(self):
        """UTF-8 文本应正确计算"""
        text = "中文测试"
        expected = hashlib.md5(text.encode("utf-8")).hexdigest()
        assert _compute_content_hash(text) == expected


class TestSyncBlogPostEmbedding:
    """测试向量同步后台任务（使用 mock 隔离外部依赖）"""

    @pytest.fixture
    def mock_embedding_client(self):
        """返回固定 1024 维全零向量的 mock embedding client"""
        mock = MagicMock()
        mock.aembed_single = AsyncMock(return_value=[0.0] * 1024)
        return mock

    @pytest.fixture
    def mock_db_session(self):
        """返回 mock 数据库 session"""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_delete_when_post_not_exist(
        self, mock_embedding_client, mock_db_session
    ):
        """文章不存在时应删除向量记录"""
        with patch(
            "app.services.vector_sync_service.SessionLocal", return_value=mock_db_session
        ), patch(
            "app.services.vector_sync_service.get_embedding_client",
            return_value=mock_embedding_client,
        ), patch(
            "app.services.vector_sync_service.get_blog_post_by_id", return_value=None
        ), patch(
            "app.services.vector_sync_service.delete_embedding_by_post_id",
            return_value=False,
        ):
            await sync_blog_post_embedding(999)
            mock_embedding_client.aembed_single.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_delete_when_post_unpublished(
        self, mock_embedding_client, mock_db_session
    ):
        """文章为 draft 状态时应删除向量记录"""
        post = MagicMock(spec=BlogPost)
        post.is_deleted = False
        post.status = "draft"

        with patch(
            "app.services.vector_sync_service.SessionLocal", return_value=mock_db_session
        ), patch(
            "app.services.vector_sync_service.get_embedding_client",
            return_value=mock_embedding_client,
        ), patch(
            "app.services.vector_sync_service.get_blog_post_by_id", return_value=post
        ), patch(
            "app.services.vector_sync_service.delete_embedding_by_post_id",
            return_value=True,
        ):
            await sync_blog_post_embedding(1)
            mock_embedding_client.aembed_single.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_skip_when_hash_unchanged(
        self, mock_embedding_client, mock_db_session
    ):
        """content_hash 未变化时应跳过 Embedding API 调用"""
        post = MagicMock(spec=BlogPost)
        post.is_deleted = False
        post.status = "published"
        post.title = "标题"
        post.category = None
        post.tags = []
        post.summary = None
        post.content_md = "正文"

        text = _build_embedding_text(post)
        existing_hash = _compute_content_hash(text)

        existing_embedding = MagicMock()
        existing_embedding.content_hash = existing_hash

        with patch(
            "app.services.vector_sync_service.SessionLocal", return_value=mock_db_session
        ), patch(
            "app.services.vector_sync_service.get_embedding_client",
            return_value=mock_embedding_client,
        ), patch(
            "app.services.vector_sync_service.get_blog_post_by_id", return_value=post
        ), patch(
            "app.services.vector_sync_service.get_embedding_by_post_id",
            return_value=existing_embedding,
        ), patch(
            "app.services.vector_sync_service.upsert_embedding"
        ) as mock_upsert:
            await sync_blog_post_embedding(1)
            mock_embedding_client.aembed_single.assert_not_awaited()
            mock_upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_when_hash_changed(
        self, mock_embedding_client, mock_db_session
    ):
        """content_hash 变化时应调用 Embedding API 并更新向量表"""
        post = MagicMock(spec=BlogPost)
        post.is_deleted = False
        post.status = "published"
        post.title = "新标题"
        post.category = None
        post.tags = []
        post.summary = None
        post.content_md = "新正文"

        existing_embedding = MagicMock()
        existing_embedding.content_hash = "old_hash"

        with patch(
            "app.services.vector_sync_service.SessionLocal", return_value=mock_db_session
        ), patch(
            "app.services.vector_sync_service.get_embedding_client",
            return_value=mock_embedding_client,
        ), patch(
            "app.services.vector_sync_service.get_blog_post_by_id", return_value=post
        ), patch(
            "app.services.vector_sync_service.get_embedding_by_post_id",
            return_value=existing_embedding,
        ), patch(
            "app.services.vector_sync_service.upsert_embedding"
        ) as mock_upsert:
            await sync_blog_post_embedding(1)
            mock_embedding_client.aembed_single.assert_awaited_once()
            mock_upsert.assert_called_once()


class TestSyncCleanupOrphanedEmbeddings:
    """测试孤立向量清理任务"""

    @pytest.mark.asyncio
    async def test_cleanup_execution(self):
        """清理任务应能正常执行 SQL 而不抛异常"""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db.execute = MagicMock(return_value=mock_result)

        with patch(
            "app.services.vector_sync_service.SessionLocal", return_value=mock_db
        ):
            await sync_cleanup_orphaned_embeddings()
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()
