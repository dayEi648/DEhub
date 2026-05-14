import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.forum_zone_service import ForumZoneService
from app.schemas.forum_zone import ForumZoneCreate, ForumZoneUpdate


class TestForumZoneServicePermission:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return ForumZoneService(db)

    @pytest.fixture
    def admin_user(self):
        user = MagicMock()
        user.permission = 1
        return user

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.permission = 0
        return user

    def test_require_admin_pass(self, service, admin_user):
        service._require_admin(admin_user)

    def test_require_admin_fail(self, service, normal_user):
        with pytest.raises(HTTPException) as exc_info:
            service._require_admin(normal_user)
        assert exc_info.value.status_code == 403

    def test_create_by_normal_user(self, db, service, normal_user):
        """普通用户创建分区应 403"""
        zone_in = ForumZoneCreate(zone_name="General", slug="general")
        with pytest.raises(HTTPException) as exc_info:
            service.create_zone(zone_in, normal_user)
        assert exc_info.value.status_code == 403

    def test_create_without_slug_auto_generates(self, db, service, admin_user):
        """未提供 slug 时应根据 zone_name 自动生成"""
        zone_in = ForumZoneCreate(zone_name="General Discussion", slug=None)
        with (
            patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug", return_value=None) as mock_get_slug,
            patch("app.services.forum_zone_service.forum_zone_crud.create_zone") as mock_create,
            patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id") as mock_get_id,
        ):
            mock_zone = MagicMock()
            mock_create.return_value = mock_zone
            mock_get_id.return_value = mock_zone

            result = service.create_zone(zone_in, admin_user)

            mock_get_slug.assert_called_once_with(db, "general-discussion")
            created_in = mock_create.call_args[0][1]
            assert created_in.slug == "general-discussion"
            assert result == mock_zone

    def test_create_with_explicit_slug_uses_provided(self, db, service, admin_user):
        """显式传入 slug 时应使用提供的值并校验唯一性"""
        zone_in = ForumZoneCreate(zone_name="General Discussion", slug="custom-zone")
        with (
            patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug", return_value=None) as mock_get_slug,
            patch("app.services.forum_zone_service.forum_zone_crud.create_zone") as mock_create,
            patch("app.services.forum_zone_service.forum_zone_crud.get_zone_by_id") as mock_get_id,
        ):
            mock_zone = MagicMock()
            mock_create.return_value = mock_zone
            mock_get_id.return_value = mock_zone

            result = service.create_zone(zone_in, admin_user)

            mock_get_slug.assert_called_once_with(db, "custom-zone")
            created_in = mock_create.call_args[0][1]
            assert created_in.slug == "custom-zone"
            assert result == mock_zone

    def test_slug_unique(self, service, admin_user):
        """重复 slug 应 400"""
        existing = MagicMock()
        existing.id = 1
        with patch(
            "app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug",
            return_value=existing,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service._ensure_slug_unique("duplicate-slug")
            assert exc_info.value.status_code == 400
            assert "slug 已存在" in exc_info.value.detail

    def test_get_zone_by_slug_found(self, db, service):
        """根据 slug 查询存在的分区应返回"""
        mock_zone = MagicMock()
        with patch(
            "app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug",
            return_value=mock_zone,
        ):
            result = service.get_zone_by_slug("general")
            assert result == mock_zone

    def test_get_zone_by_slug_not_found(self, db, service):
        """根据 slug 查询不存在的分区应 404"""
        with patch(
            "app.services.forum_zone_service.forum_zone_crud.get_zone_by_slug",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.get_zone_by_slug("not-exist")
            assert exc_info.value.status_code == 404
            assert "分区不存在" in exc_info.value.detail


class TestForumZoneSchema:
    def test_create_valid(self):
        zone = ForumZoneCreate(zone_name="General", slug="general")
        assert zone.zone_name == "General"
        assert zone.slug == "general"

    def test_create_without_slug(self):
        """未提供 slug 时应通过校验"""
        zone = ForumZoneCreate(zone_name="General", slug=None)
        assert zone.zone_name == "General"
        assert zone.slug is None

    def test_create_name_too_long(self):
        with pytest.raises(Exception):
            ForumZoneCreate(zone_name="x" * 65, slug="general")

    def test_update_empty(self):
        update = ForumZoneUpdate()
        assert update.zone_name is None
        assert update.slug is None

    def test_update_partial(self):
        update = ForumZoneUpdate(zone_name="New Name")
        assert update.zone_name == "New Name"
        assert update.slug is None
