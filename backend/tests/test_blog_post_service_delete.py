"""
测试博客文章删除时的级联清理逻辑
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.blog_post_service import BlogPostService


@pytest.mark.asyncio
@patch("app.services.blog_post_service.asyncio.to_thread", new_callable=AsyncMock)
@patch("app.services.blog_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.blog_post_service.delete_file_from_oss")
@patch("app.services.blog_post_service.blog_post_crud.hard_delete_blog_post")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
async def test_hard_delete_blog_post_cleans_embedded_images(
    mock_get_blog_post_by_id,
    mock_hard_delete,
    mock_delete_file_from_oss,
    mock_extract_urls,
    _mock_to_thread,
):
    db = MagicMock()
    service = BlogPostService(db)

    current_user = MagicMock()
    current_user.permission = 2

    db_post = MagicMock()
    db_post.id = 42
    db_post.cover_image_url = "https://cdn.example.com/covers/old.jpg"
    db_post.content_md = "# 标题\n![图](https://cdn.example.com/uploads/images/20240101/abc.jpg)"
    db_post.status = "published"

    mock_get_blog_post_by_id.return_value = db_post
    mock_extract_urls.return_value = [
        "https://cdn.example.com/uploads/images/20240101/abc.jpg",
        "https://cdn.example.com/uploads/images/20240102/def.png",
    ]
    mock_hard_delete.return_value = 1

    await service.hard_delete_blog_post(42, current_user)

    # 封面图应被删除
    assert mock_delete_file_from_oss.await_count == 3
    calls = [str(c) for c in mock_delete_file_from_oss.await_args_list]
    assert any("covers/old.jpg" in c for c in calls)
    assert any("uploads/images/20240101/abc.jpg" in c for c in calls)
    assert any("uploads/images/20240102/def.png" in c for c in calls)
    mock_hard_delete.assert_called_once_with(db, 42)


@pytest.mark.asyncio
@patch("app.services.blog_post_service.asyncio.to_thread", new_callable=AsyncMock)
@patch("app.services.blog_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.blog_post_service.delete_file_from_oss")
@patch("app.services.blog_post_service.blog_post_crud.hard_delete_blog_post")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
async def test_hard_delete_embedded_image_fail_should_not_block_deletion(
    mock_get_blog_post_by_id,
    mock_hard_delete,
    mock_delete_file_from_oss,
    mock_extract_urls,
    _mock_to_thread,
):
    db = MagicMock()
    service = BlogPostService(db)

    current_user = MagicMock()
    current_user.permission = 2

    db_post = MagicMock()
    db_post.id = 99
    db_post.cover_image_url = None
    db_post.content_md = "![图](https://cdn.example.com/uploads/images/20240101/abc.jpg)"

    mock_get_blog_post_by_id.return_value = db_post
    mock_extract_urls.return_value = ["https://cdn.example.com/uploads/images/20240101/abc.jpg"]
    # 模拟正文图片删除失败
    mock_delete_file_from_oss.side_effect = Exception("OSS delete failed")
    mock_hard_delete.return_value = 1

    # 不应抛出异常
    await service.hard_delete_blog_post(99, current_user)

    mock_delete_file_from_oss.assert_awaited_once()
    mock_hard_delete.assert_called_once_with(db, 99)


@pytest.mark.asyncio
@patch("app.services.blog_post_service.asyncio.to_thread", new_callable=AsyncMock)
@patch("app.services.blog_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.blog_post_service.delete_file_from_oss")
@patch("app.services.blog_post_service.blog_post_crud.hard_delete_blog_post")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
async def test_hard_delete_no_embedded_images_should_only_delete_cover(
    mock_get_blog_post_by_id,
    mock_hard_delete,
    mock_delete_file_from_oss,
    mock_extract_urls,
    _mock_to_thread,
):
    db = MagicMock()
    service = BlogPostService(db)

    current_user = MagicMock()
    current_user.permission = 2

    db_post = MagicMock()
    db_post.id = 7
    db_post.cover_image_url = "https://cdn.example.com/covers/cover.jpg"
    db_post.content_md = "纯文本没有图片"

    mock_get_blog_post_by_id.return_value = db_post
    mock_extract_urls.return_value = []
    mock_hard_delete.return_value = 1

    await service.hard_delete_blog_post(7, current_user)

    mock_extract_urls.assert_called_once_with("纯文本没有图片")
    assert mock_delete_file_from_oss.await_count == 1
    mock_hard_delete.assert_called_once_with(db, 7)


@pytest.mark.asyncio
@patch("app.services.blog_post_service.asyncio.to_thread", new_callable=AsyncMock)
@patch("app.services.blog_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.blog_post_service.delete_file_from_oss")
@patch("app.services.blog_post_service.blog_post_crud.hard_delete_blog_post")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
async def test_hard_delete_db_not_found_should_not_delete_oss_files(
    mock_get_blog_post_by_id,
    mock_hard_delete,
    mock_delete_file_from_oss,
    mock_extract_urls,
    _mock_to_thread,
):
    db = MagicMock()
    service = BlogPostService(db)

    current_user = MagicMock()
    current_user.permission = 2

    db_post = MagicMock()
    db_post.id = 7
    db_post.cover_image_url = "https://cdn.example.com/covers/cover.jpg"
    db_post.content_md = "![图](https://cdn.example.com/uploads/images/a.jpg)"

    mock_get_blog_post_by_id.return_value = db_post
    mock_extract_urls.return_value = ["https://cdn.example.com/uploads/images/a.jpg"]
    mock_hard_delete.return_value = 0

    with pytest.raises(Exception):
        await service.hard_delete_blog_post(7, current_user)

    mock_delete_file_from_oss.assert_not_called()
