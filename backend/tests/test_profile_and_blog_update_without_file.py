from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.blog_post import BlogPostUpdate
from app.schemas.user import UserUpdate
from app.services.blog_post_service import BlogPostService
from app.services.user_service import UserService


@pytest.mark.asyncio
@patch("app.services.user_service.upload_image")
@patch("app.services.user_service.delete_file_from_oss")
@patch("app.services.user_service.user_crud.update_user")
@patch("app.services.user_service.user_crud.get_user_by_id")
async def test_update_user_without_file_should_not_touch_avatar(
    mock_get_user_by_id,
    mock_update_user,
    mock_delete_file_from_oss,
    mock_upload_image,
):
    db = MagicMock()
    service = UserService(db)

    current_user = MagicMock()
    current_user.id = 1
    current_user.permission = 0

    db_user = SimpleNamespace(
        id=1,
        username="old_name",
        email="old@example.com",
        created_at=datetime.now(),
        permission=0,
        is_deleted=False,
        avatar_url="https://oss.example.com/avatar/old.jpg",
        personal_profile="old profile",
    )

    mock_get_user_by_id.return_value = db_user
    mock_update_user.return_value = db_user

    user_in = UserUpdate(personal_profile="new profile")
    await service.update_user(1, user_in, current_user, file=None)

    mock_delete_file_from_oss.assert_not_called()
    mock_upload_image.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.blog_post_service.asyncio.to_thread", new_callable=AsyncMock)
@patch("app.services.blog_post_service.upload_image")
@patch("app.services.blog_post_service.delete_file_from_oss")
@patch("app.services.blog_post_service.blog_post_crud.update_blog_post")
@patch("app.services.blog_post_service.blog_post_crud.get_blog_post_by_id")
async def test_update_blog_post_without_file_should_not_replace_cover(
    mock_get_blog_post_by_id,
    mock_update_blog_post,
    mock_delete_file_from_oss,
    mock_upload_image,
    _mock_to_thread,
):
    db = MagicMock()
    service = BlogPostService(db)

    current_user = MagicMock()
    current_user.permission = 2

    db_post = MagicMock()
    db_post.id = 100
    db_post.slug = "old-slug"
    db_post.status = "draft"
    db_post.cover_image_url = "https://oss.example.com/covers/old.jpg"

    mock_get_blog_post_by_id.side_effect = [db_post, db_post]
    mock_update_blog_post.return_value = db_post

    post_in = BlogPostUpdate(title="new title")
    await service.update_blog_post(100, post_in, current_user, file=None)

    mock_delete_file_from_oss.assert_not_called()
    mock_upload_image.assert_not_called()
