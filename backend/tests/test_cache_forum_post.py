"""论坛帖子列表缓存集成测试。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.forum_post import ForumPostListResponse, ForumPostResponse
from app.services.forum_post_service import ForumPostService
from app.services.forum_reply_service import ForumReplyService


def _make_mock_post():
    """构造可用于 ForumPostResponse.model_validate 的 mock post。"""
    post = MagicMock()
    post.id = 1
    post.user_id = 1
    post.title = "Test"
    post.content = "content"
    post.zone_id = 1
    post.view_count = 0
    post.reply_count = 0
    post.created_at = datetime.now(timezone.utc)
    post.updated_at = datetime.now(timezone.utc)
    post.user = MagicMock()
    post.user.id = 1
    post.user.username = "user"
    post.user.avatar_url = None
    return post


class TestForumPostListCache:
    """测试论坛帖子列表缓存。"""

    @patch("app.services.forum_post_service.get_json_cache")
    @patch("app.services.forum_post_service.set_json_cache")
    @patch("app.services.forum_post_service.forum_post_crud.get_posts")
    @patch("app.services.forum_post_service.forum_zone_crud.get_zone_by_id")
    def test_first_call_queries_db_and_sets_cache(
        self, mock_get_zone, mock_get_posts, mock_set_cache, mock_get_cache
    ):
        mock_get_cache.return_value = None
        mock_get_zone.return_value = MagicMock()
        mock_get_posts.return_value = ([_make_mock_post()], 1)

        db = MagicMock()
        service = ForumPostService(db)

        result = service.list_posts(zone_id=1, sort_by="created", skip=0, limit=10)
        assert isinstance(result, ForumPostListResponse)
        assert result.total == 1
        mock_get_posts.assert_called_once()
        mock_set_cache.assert_called_once()

    @patch("app.services.forum_post_service.get_json_cache")
    @patch("app.services.forum_post_service.set_json_cache")
    @patch("app.services.forum_post_service.forum_post_crud.get_posts")
    def test_second_call_hits_cache(self, mock_get_posts, mock_set_cache, mock_get_cache):
        cached = ForumPostListResponse(items=[], total=0)
        mock_get_cache.return_value = cached

        db = MagicMock()
        service = ForumPostService(db)

        result = service.list_posts(zone_id=1, sort_by="created", skip=0, limit=10)
        assert result is cached
        mock_get_posts.assert_not_called()
        mock_set_cache.assert_not_called()

    @patch("app.services.forum_post_service.acquire_cache_lock")
    @patch("app.services.forum_post_service.get_json_cache")
    @patch("app.services.forum_post_service.set_json_cache")
    @patch("app.services.forum_post_service.forum_post_crud.get_posts")
    @patch("app.services.forum_post_service.forum_zone_crud.get_zone_by_id")
    def test_hot_sort_uses_shorter_ttl(self, mock_get_zone, mock_get_posts, mock_set_cache, mock_get_cache, mock_lock):
        mock_get_cache.return_value = None
        mock_lock.return_value = "token"
        mock_get_zone.return_value = MagicMock()
        mock_get_posts.return_value = ([_make_mock_post()], 1)

        db = MagicMock()
        service = ForumPostService(db)

        service.list_posts(zone_id=None, sort_by="view", skip=0, limit=6)
        _, _, ttl = mock_set_cache.call_args[0]
        # 热门 TTL 应使用 CACHE_FORUM_HOT_POST_TTL (30)
        assert ttl == 30

    @patch("app.services.forum_post_service.release_cache_lock")
    @patch("app.services.forum_post_service.acquire_cache_lock")
    @patch("app.services.forum_post_service.get_json_cache")
    @patch("app.services.forum_post_service.set_json_cache")
    @patch("app.services.forum_post_service.forum_post_crud.get_posts")
    def test_hot_key_lock_acquired_writes_cache(
        self, mock_get_posts, mock_set_cache, mock_get_cache, mock_lock, mock_release
    ):
        """热门 key 抢到锁后应写缓存并释放锁。"""
        mock_get_cache.return_value = None
        mock_lock.return_value = "token"
        mock_get_posts.return_value = ([_make_mock_post()], 1)

        db = MagicMock()
        service = ForumPostService(db)

        service.list_posts(zone_id=None, sort_by="view", skip=0, limit=6)
        mock_lock.assert_called_once()
        mock_set_cache.assert_called_once()
        mock_release.assert_called_once()

    @patch("app.services.forum_post_service.release_cache_lock")
    @patch("app.services.forum_post_service.acquire_cache_lock")
    @patch("app.services.forum_post_service.get_json_cache")
    @patch("app.services.forum_post_service.set_json_cache")
    @patch("app.services.forum_post_service.forum_post_crud.get_posts")
    def test_hot_key_lock_miss_skips_cache_write(
        self, mock_get_posts, mock_set_cache, mock_get_cache, mock_lock, mock_release
    ):
        """热门 key 未抢到锁时，应走数据库但不写缓存。"""
        mock_get_cache.return_value = None
        mock_lock.return_value = None
        mock_get_posts.return_value = ([_make_mock_post()], 1)

        db = MagicMock()
        service = ForumPostService(db)

        service.list_posts(zone_id=None, sort_by="view", skip=0, limit=6)
        mock_lock.assert_called_once()
        mock_set_cache.assert_not_called()
        mock_release.assert_not_called()


class TestForumPostCacheInvalidation:
    """测试帖子写操作后缓存失效。"""

    @patch("app.services.forum_post_service.ForumCacheInvalidator.invalidate_forum_posts")
    @patch("app.services.forum_post_service.forum_post_crud.create_post")
    @patch("app.services.forum_post_service.forum_post_crud.get_post_by_id")
    @patch("app.services.forum_post_service.forum_zone_crud.get_zone_by_id")
    def test_create_post_invalidates_cache(
        self, mock_get_zone, mock_get_post, mock_create, mock_invalidate
    ):
        db = MagicMock()
        service = ForumPostService(db)
        current_user = MagicMock()
        current_user.id = 1

        mock_get_zone.return_value = MagicMock()
        mock_create.return_value = MagicMock()
        mock_get_post.return_value = _make_mock_post()

        post_in = MagicMock()
        post_in.zone_id = 1

        service.create_post(post_in, current_user)
        mock_invalidate.assert_called_once_with(zone_id=1)

    @patch("app.services.forum_post_service.ForumCacheInvalidator.invalidate_forum_posts_for_zone_change")
    @patch("app.services.forum_post_service.forum_post_crud.update_post")
    @patch("app.services.forum_post_service.forum_post_crud.get_post_by_id")
    def test_update_post_zone_change_invalidates_both_zones(
        self, mock_get_post, mock_update, mock_invalidate
    ):
        db = MagicMock()
        service = ForumPostService(db)
        current_user = MagicMock()
        current_user.permission = 1
        current_user.id = 1

        db_post = _make_mock_post()
        db_post.user_id = 1
        db_post.zone_id = 1
        mock_get_post.return_value = db_post

        updated = _make_mock_post()
        updated.zone_id = 2
        mock_update.return_value = updated

        post_in = MagicMock()
        post_in.model_dump.return_value = {"zone_id": 2}

        service.update_post(1, post_in, current_user)
        mock_invalidate.assert_called_once_with(old_zone_id=1, new_zone_id=2)

    @patch("app.services.forum_post_service.is_zone_manager")
    @patch("app.services.forum_post_service.ForumCacheInvalidator.invalidate_forum_posts")
    @patch("app.services.forum_post_service.forum_post_crud.delete_post")
    @patch("app.services.forum_post_service.forum_post_crud.get_post_by_id")
    def test_delete_post_invalidates_cache(
        self, mock_get_post, mock_delete, mock_invalidate, mock_is_manager
    ):
        db = MagicMock()
        service = ForumPostService(db)
        current_user = MagicMock()
        current_user.permission = 1
        current_user.id = 1

        mock_is_manager.return_value = False
        db_post = _make_mock_post()
        db_post.user_id = 1
        mock_get_post.return_value = db_post

        service.delete_post(1, current_user)
        mock_invalidate.assert_called_once_with(zone_id=1)


class TestForumReplyCacheInvalidation:
    """测试回复操作后帖子列表缓存失效。"""

    @patch("app.services.forum_reply_service.ForumCacheInvalidator.invalidate_forum_posts")
    @patch("app.services.forum_reply_service.forum_reply_crud.create_reply")
    @patch("app.services.forum_reply_service.forum_post_crud.increment_reply_count")
    @patch("app.services.forum_reply_service.forum_post_crud.get_post_by_id")
    def test_create_reply_invalidates_zone_cache(
        self, mock_get_post, mock_inc, mock_create, mock_invalidate
    ):
        db = MagicMock()
        service = ForumReplyService(db)
        current_user = MagicMock()
        current_user.id = 1

        mock_post = MagicMock()
        mock_post.zone_id = 1
        mock_get_post.return_value = mock_post

        mock_reply = MagicMock()
        mock_create.return_value = mock_reply

        reply_in = MagicMock()
        service.create_reply(1, reply_in, current_user)
        mock_invalidate.assert_called_once_with(zone_id=1)

    @patch("app.services.forum_reply_service.is_zone_manager")
    @patch("app.services.forum_reply_service.ForumCacheInvalidator.invalidate_forum_posts")
    @patch("app.services.forum_reply_service.forum_reply_crud.delete_reply")
    @patch("app.services.forum_reply_service.forum_post_crud.decrement_reply_count")
    @patch("app.services.forum_reply_service.forum_reply_crud.get_reply_by_id")
    @patch("app.services.forum_reply_service.forum_post_crud.get_post_by_id")
    def test_delete_reply_invalidates_zone_cache(
        self, mock_get_post, mock_get_reply, mock_dec, mock_delete, mock_invalidate, mock_is_manager
    ):
        db = MagicMock()
        service = ForumReplyService(db)
        current_user = MagicMock()
        current_user.permission = 1
        current_user.id = 1

        mock_is_manager.return_value = False
        mock_post = MagicMock()
        mock_post.zone_id = 1
        mock_get_post.return_value = mock_post

        db_reply = MagicMock()
        db_reply.user_id = 1
        db_reply.post_id = 1
        db_reply.content = "test content"
        mock_get_reply.return_value = db_reply

        service.delete_reply(1, current_user)
        mock_invalidate.assert_called_once_with(zone_id=1)
