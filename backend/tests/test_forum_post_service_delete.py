from unittest.mock import MagicMock, patch

import pytest

from app.services.forum_post_service import ForumPostService


@patch("app.services.forum_post_service.forum_post_crud")
@patch("app.services.forum_post_service.forum_reply_crud")
@patch("app.services.forum_post_service.comment_crud")
@patch("app.services.forum_post_service.is_zone_manager")
@patch("app.services.forum_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.forum_post_service.convert_oss_url_to_file_path")
@patch("app.services.forum_post_service.delete_file_from_oss_sync")
def test_delete_post_cascades_reply_comments_and_embedded_images(
    mock_delete_file,
    mock_convert_path,
    mock_extract_urls,
    mock_is_manager,
    mock_comment_crud,
    mock_reply_crud,
    mock_post_crud,
):
    db = MagicMock()
    service = ForumPostService(db)

    current_user = MagicMock()
    current_user.id = 1
    current_user.permission = 0

    db_post = MagicMock()
    db_post.id = 100
    db_post.user_id = 1
    db_post.zone_id = 9
    db_post.content = "post markdown"
    mock_post_crud.get_post_by_id.return_value = db_post

    reply1 = MagicMock()
    reply1.id = 201
    reply1.content = "reply one"
    reply2 = MagicMock()
    reply2.id = 202
    reply2.content = "reply two"
    mock_reply_crud.get_all_replies_by_post_id.return_value = [reply1, reply2]
    mock_is_manager.return_value = False

    mock_extract_urls.side_effect = [
        ["https://oss.example.com/forum/posts/20260101/post.jpg"],
        ["https://oss.example.com/forum/replies/20260101/reply1.jpg"],
        ["https://oss.example.com/forum/replies/20260101/reply2.jpg"],
    ]
    mock_convert_path.side_effect = [
        "forum/posts/20260101/post.jpg",
        "forum/replies/20260101/reply1.jpg",
        "forum/replies/20260101/reply2.jpg",
    ]
    mock_comment_crud.get_comment_ids_by_target_ids.return_value = [301, 302]

    service.delete_post(100, current_user)

    mock_comment_crud.get_comment_ids_by_target_ids.assert_called_once_with(
        db,
        target_type="forum_reply",
        target_ids=[201, 202],
    )
    mock_comment_crud.delete_comment_likes_by_comment_ids.assert_called_once_with(db, [301, 302])
    mock_comment_crud.delete_comments_by_ids.assert_called_once_with(db, [301, 302])
    assert mock_delete_file.call_count == 3
    mock_post_crud.delete_post.assert_called_once_with(db, 100)


@patch("app.services.forum_post_service.forum_post_crud")
@patch("app.services.forum_post_service.forum_reply_crud")
@patch("app.services.forum_post_service.comment_crud")
@patch("app.services.forum_post_service.is_zone_manager")
@patch("app.services.forum_post_service.extract_oss_image_urls_from_markdown")
@patch("app.services.forum_post_service.convert_oss_url_to_file_path")
@patch("app.services.forum_post_service.delete_file_from_oss_sync")
def test_delete_post_db_failure_should_not_delete_oss_files(
    mock_delete_file,
    mock_convert_path,
    mock_extract_urls,
    mock_is_manager,
    mock_comment_crud,
    mock_reply_crud,
    mock_post_crud,
):
    db = MagicMock()
    service = ForumPostService(db)

    current_user = MagicMock()
    current_user.id = 1
    current_user.permission = 0

    db_post = MagicMock()
    db_post.id = 100
    db_post.user_id = 1
    db_post.zone_id = 9
    db_post.content = "post markdown"
    mock_post_crud.get_post_by_id.return_value = db_post
    mock_reply_crud.get_all_replies_by_post_id.return_value = []
    mock_is_manager.return_value = False
    mock_extract_urls.return_value = ["https://oss.example.com/forum/posts/a.jpg"]
    mock_convert_path.return_value = "forum/posts/a.jpg"
    mock_comment_crud.get_comment_ids_by_target_ids.return_value = []
    mock_post_crud.delete_post.side_effect = RuntimeError("db failed")

    with pytest.raises(RuntimeError):
        service.delete_post(100, current_user)

    mock_delete_file.assert_not_called()
