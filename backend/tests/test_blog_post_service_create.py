from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.blog_post import BlogPostCreate
from app.services.blog_post_service import BlogPostService


@pytest.mark.asyncio
@patch("app.services.blog_post_service.upload_image")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_slug")
@patch("app.services.blog_post_service.blog_post_crud.create_blog_post")
async def test_create_blog_post_upload_fail_should_not_create_post(
    mock_create_blog_post,
    mock_get_blog_post_by_slug,
    mock_upload_image,
):
    db = MagicMock()
    service = BlogPostService(db)
    current_user = MagicMock()
    current_user.permission = 2

    post_in = BlogPostCreate(
        title="t",
        slug="test-slug",
        summary="s",
        content_md="c",
        category_id=1,
        tags=[],
        status="draft",
    )

    mock_get_blog_post_by_slug.return_value = None
    mock_upload_image.side_effect = HTTPException(status_code=413, detail="图片压缩后仍超过大小限制")
    file_obj = MagicMock()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_blog_post(post_in, current_user, file_obj)

    assert exc_info.value.status_code == 413
    mock_create_blog_post.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.blog_post_service.OssCleanupService.delete_file_after_commit", new_callable=AsyncMock)
@patch("app.services.blog_post_service.upload_image")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_slug")
@patch("app.services.blog_post_service.blog_post_crud.create_blog_post")
async def test_create_blog_post_db_failure_should_cleanup_uploaded_cover(
    mock_create_blog_post,
    mock_get_blog_post_by_slug,
    mock_upload_image,
    mock_cleanup_file,
):
    db = MagicMock()
    service = BlogPostService(db)
    current_user = MagicMock()
    current_user.permission = 2

    post_in = BlogPostCreate(
        title="t",
        slug="test-slug",
        summary="s",
        content_md="c",
        category_id=1,
        tags=[],
        status="draft",
    )

    mock_get_blog_post_by_slug.return_value = None
    mock_upload_image.return_value = "https://oss.example.com/covers/new.jpg"
    mock_create_blog_post.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError):
        await service.create_blog_post(post_in, current_user, MagicMock())

    mock_cleanup_file.assert_awaited_once()
    assert "covers/new.jpg" in str(mock_cleanup_file.await_args)
