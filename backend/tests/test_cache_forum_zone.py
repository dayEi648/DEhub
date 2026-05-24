"""论坛分区缓存集成测试。"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.forum_zone import ForumZoneResponse
from app.services.forum_zone_service import ForumZoneService


def _make_mock_zone():
    """构造可用于 ForumZoneResponse.model_validate 的 mock zone。"""
    zone = MagicMock()
    zone.id = 1
    zone.slug = "test"
    zone.zone_name = "Test Zone"
    zone.description = None
    zone.manager_id = 1
    zone.view_count = 0
    zone.created_at = datetime.now(timezone.utc)
    zone.manager = MagicMock()
    zone.manager.id = 1
    zone.manager.username = "manager"
    zone.manager.avatar_url = None
    return zone


class TestForumZoneListCache:
    """测试论坛分区列表缓存。"""

    @patch("app.services.forum_zone_service.get_json_cache")
    @patch("app.services.forum_zone_service.set_json_cache")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_all_zones")
    def test_first_call_queries_db_and_sets_cache(
        self, mock_get_all, mock_set_cache, mock_get_cache
    ):
        mock_get_cache.return_value = None
        mock_get_all.return_value = [_make_mock_zone()]

        db = MagicMock()
        service = ForumZoneService(db)

        result = service.list_zones()
        assert isinstance(result, list)
        assert len(result) == 1
        mock_get_all.assert_called_once()
        mock_set_cache.assert_called_once()

    @patch("app.services.forum_zone_service.get_json_cache")
    @patch("app.services.forum_zone_service.set_json_cache")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_all_zones")
    def test_second_call_hits_cache(self, mock_get_all, mock_set_cache, mock_get_cache):
        cached = [ForumZoneResponse.model_validate(_make_mock_zone())]
        mock_get_cache.return_value = cached

        db = MagicMock()
        service = ForumZoneService(db)

        result = service.list_zones()
        assert result is cached
        mock_get_all.assert_not_called()
        mock_set_cache.assert_not_called()


class TestForumZoneDetailCache:
    """测试论坛分区详情缓存。"""

    @patch("app.services.forum_zone_service.get_json_cache")
    @patch("app.services.forum_zone_service.set_json_cache")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id")
    def test_get_zone_first_call_sets_cache(self, mock_get_zone, mock_set_cache, mock_get_cache):
        mock_get_cache.return_value = None
        mock_get_zone.return_value = _make_mock_zone()

        db = MagicMock()
        service = ForumZoneService(db)

        result = service.get_zone(1)
        assert result.id == 1
        mock_get_zone.assert_called_once()
        mock_set_cache.assert_called_once()

    @patch("app.services.forum_zone_service.get_json_cache")
    @patch("app.services.forum_zone_service.set_json_cache")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug")
    def test_get_zone_by_slug_first_call_sets_cache(
        self, mock_get_slug, mock_set_cache, mock_get_cache
    ):
        mock_get_cache.return_value = None
        mock_get_slug.return_value = _make_mock_zone()

        db = MagicMock()
        service = ForumZoneService(db)

        result = service.get_zone_by_slug("test")
        assert result.zone_name == "Test Zone"
        mock_get_slug.assert_called_once()
        mock_set_cache.assert_called_once()

    @patch("app.services.forum_zone_service.get_json_cache")
    @patch("app.services.forum_zone_service.set_json_cache")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id")
    def test_get_zone_second_call_hits_cache(self, mock_get_zone, mock_set_cache, mock_get_cache):
        cached = ForumZoneResponse.model_validate(_make_mock_zone())
        mock_get_cache.return_value = cached

        db = MagicMock()
        service = ForumZoneService(db)

        result = service.get_zone(1)
        assert result is cached
        mock_get_zone.assert_not_called()
        mock_set_cache.assert_not_called()


class TestForumZoneCacheInvalidation:
    """测试分区写操作后缓存失效。"""

    @patch("app.services.forum_zone_service.delete_zone_manager_cache")
    @patch("app.services.forum_zone_service.ForumCacheInvalidator.invalidate_forum_zones")
    @patch("app.services.forum_zone_service.forum_zone_crud.create_zone")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug")
    @patch("app.services.forum_zone_service.user_crud.get_user_by_id")
    def test_create_zone_invalidates_cache(
        self, mock_get_user, mock_get_slug, mock_get_id, mock_create, mock_invalidate, mock_delete_cache
    ):
        db = MagicMock()
        service = ForumZoneService(db)
        current_user = MagicMock()
        current_user.permission = 1
        current_user.id = 1

        mock_user = MagicMock()
        mock_user.is_deleted = False
        mock_get_user.return_value = mock_user
        mock_get_slug.return_value = None
        zone_in = MagicMock()
        zone_in.slug = "test"
        zone_in.zone_name = "Test"
        zone_in.manager_id = None
        zone_in.model_dump.return_value = {"zone_name": "Test", "slug": "test"}

        mock_create.return_value = MagicMock()
        mock_get_id.return_value = _make_mock_zone()

        service.create_zone(zone_in, current_user)
        mock_invalidate.assert_called_once()

    @patch("app.services.forum_zone_service.ForumCacheInvalidator.invalidate_forum_zones")
    @patch("app.services.forum_zone_service.forum_zone_crud.update_zone")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id")
    @patch("app.services.forum_zone_service.is_zone_manager")
    def test_update_zone_invalidates_cache(
        self, mock_is_manager, mock_get_id, mock_update, mock_invalidate
    ):
        db = MagicMock()
        service = ForumZoneService(db)
        current_user = MagicMock()
        current_user.permission = 1
        current_user.id = 1

        mock_get_id.return_value = _make_mock_zone()
        mock_is_manager.return_value = False
        mock_update.return_value = _make_mock_zone()

        zone_in = MagicMock()
        zone_in.model_dump.return_value = {"zone_name": "Updated"}

        service.update_zone(1, zone_in, current_user)
        mock_invalidate.assert_called_once()

    @patch("app.services.forum_zone_service.delete_zone_manager_cache")
    @patch("app.services.forum_zone_service.ForumCacheInvalidator.invalidate_forum_zones")
    @patch("app.services.forum_zone_service.forum_zone_crud.delete_zone")
    @patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id")
    @patch("app.services.forum_zone_service.forum_post_crud.get_posts")
    def test_delete_zone_invalidates_cache(
        self, mock_get_posts, mock_get_id, mock_delete, mock_invalidate, mock_delete_cache
    ):
        db = MagicMock()
        service = ForumZoneService(db)
        current_user = MagicMock()
        current_user.permission = 1

        mock_get_id.return_value = _make_mock_zone()
        mock_get_posts.return_value = ([], 0)
        mock_delete.return_value = 1

        service.delete_zone(1, current_user)
        mock_invalidate.assert_called_once()
