from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.user_favorite_service import UserFavoriteService


@patch("app.services.user_favorite_service.favorite_crud")
@patch("app.services.user_favorite_service.blog_post_crud")
def test_blog_post_favorite_status_should_validate_visible_post(
    mock_blog_post_crud,
    mock_favorite_crud,
):
    service = UserFavoriteService(MagicMock())
    current_user = MagicMock()
    current_user.id = 1
    current_user.permission = 0

    mock_blog_post_crud.get_blog_post_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.is_blog_post_favorited(999, current_user)

    assert exc_info.value.status_code == 404
    mock_favorite_crud.get_blog_post_favorite.assert_not_called()


@patch("app.services.user_favorite_service.favorite_crud")
@patch("app.services.user_favorite_service.forum_post_crud")
def test_forum_post_favorite_status_should_validate_post_exists(
    mock_forum_post_crud,
    mock_favorite_crud,
):
    service = UserFavoriteService(MagicMock())
    current_user = MagicMock()
    current_user.id = 1

    mock_forum_post_crud.get_post_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.is_post_favorited(999, current_user)

    assert exc_info.value.status_code == 404
    mock_favorite_crud.get_post_favorite.assert_not_called()
