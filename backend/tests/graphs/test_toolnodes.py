"""Tool 节点单元测试。"""

from unittest.mock import MagicMock, patch

import pytest

from app.graphs.nodes.toolnodes.list_blog_categories import list_blog_categories


class TestListBlogCategories:
    @patch("app.graphs.nodes.toolnodes.list_blog_categories.SessionLocal")
    def test_returns_categories_with_post_count(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        mock_cat1 = MagicMock()
        mock_cat1.name = "技术随笔"
        mock_cat1.slug = "tech"
        mock_cat1.description = "技术类文章"

        mock_cat2 = MagicMock()
        mock_cat2.name = "生活随想"
        mock_cat2.slug = "life"
        mock_cat2.description = None

        with patch(
            "app.graphs.nodes.toolnodes.list_blog_categories.blog_category_crud.get_all_categories",
            return_value=[mock_cat1, mock_cat2],
        ) as mock_get_all, patch(
            "app.graphs.nodes.toolnodes.list_blog_categories.blog_category_crud.count_posts_in_category",
            side_effect=[5, 3],
        ) as mock_count:
            result = list_blog_categories.invoke({})

        assert "技术随笔" in result
        assert "生活随想" in result
        assert "已发布文章 5 篇" in result
        assert "已发布文章 3 篇" in result
        assert "技术类文章" in result
        mock_get_all.assert_called_once_with(mock_db)
        mock_count.assert_any_call(mock_db, mock_cat1.id, status="published")
        mock_count.assert_any_call(mock_db, mock_cat2.id, status="published")

    @patch("app.graphs.nodes.toolnodes.list_blog_categories.SessionLocal")
    def test_returns_no_categories_message(self, mock_session_local):
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db

        with patch(
            "app.graphs.nodes.toolnodes.list_blog_categories.blog_category_crud.get_all_categories",
            return_value=[],
        ):
            result = list_blog_categories.invoke({})

        assert "当前网站暂无博客分类" in result
