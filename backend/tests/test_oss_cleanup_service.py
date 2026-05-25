from unittest.mock import AsyncMock, patch

import pytest

from app.models.oss_cleanup_task import OssCleanupTask
from app.models.user import User
from app.services.oss_cleanup_service import OssCleanupService


@pytest.mark.asyncio
async def test_async_cleanup_failure_is_persisted_for_retry(db_session):
    service = OssCleanupService()

    with patch(
        "app.services.oss_cleanup_service.delete_file_from_oss",
        new=AsyncMock(side_effect=RuntimeError("oss unavailable")),
    ):
        task = await service.delete_file_after_commit(
            file_path="avatars/old.png",
            source="user.avatar",
        )

    persisted = db_session.get(OssCleanupTask, task.id)
    assert persisted is not None
    assert persisted.file_path == "avatars/old.png"
    assert persisted.source == "user.avatar"
    assert persisted.status == "failed"
    assert persisted.retry_count == 1
    assert "oss unavailable" in persisted.last_error
    assert persisted.next_retry_at is not None


@pytest.mark.asyncio
async def test_async_cleanup_success_is_persisted(db_session):
    service = OssCleanupService()

    with patch(
        "app.services.oss_cleanup_service.delete_file_from_oss",
        new=AsyncMock(return_value=None),
    ):
        task = await service.delete_file_after_commit(
            file_path="covers/old.jpg",
            source="blog.cover",
        )

    persisted = db_session.get(OssCleanupTask, task.id)
    assert persisted is not None
    assert persisted.status == "succeeded"
    assert persisted.retry_count == 0
    assert persisted.last_error is None
    assert persisted.next_retry_at is None


def test_sync_cleanup_failure_is_persisted_for_retry(db_session):
    service = OssCleanupService()

    with patch(
        "app.services.oss_cleanup_service.delete_file_from_oss_sync",
        side_effect=RuntimeError("sync oss unavailable"),
    ):
        task = service.delete_file_after_commit_sync(
            file_path="forum/posts/a.png",
            source="forum.post",
        )

    persisted = db_session.get(OssCleanupTask, task.id)
    assert persisted is not None
    assert persisted.status == "failed"
    assert persisted.retry_count == 1
    assert "sync oss unavailable" in persisted.last_error


@pytest.mark.asyncio
async def test_async_cleanup_task_creation_failure_does_not_raise(db_session):
    service = OssCleanupService()

    with (
        patch.object(service, "_create_task", side_effect=RuntimeError("db down")),
        patch(
            "app.services.oss_cleanup_service.delete_file_from_oss",
            new=AsyncMock(return_value=None),
        ) as delete_mock,
    ):
        task = await service.delete_file_after_commit(
            file_path="avatars/orphan.png",
            source="user.avatar",
        )

    assert task is None
    delete_mock.assert_not_awaited()


def test_sync_cleanup_task_creation_failure_does_not_raise(db_session):
    service = OssCleanupService()

    with (
        patch.object(service, "_create_task", side_effect=RuntimeError("db down")),
        patch("app.services.oss_cleanup_service.delete_file_from_oss_sync") as delete_mock,
    ):
        task = service.delete_file_after_commit_sync(
            file_path="covers/orphan.jpg",
            source="blog.cover",
        )

    assert task is None
    delete_mock.assert_not_called()


def test_sync_cleanup_does_not_commit_caller_pending_changes(db_session):
    pending_user = User(
        username="pending_cleanup_user",
        email="pending_cleanup_user@test.com",
        hashed_password="$2b$12$dummyhashedpassword",
        permission=0,
    )
    db_session.add(pending_user)
    service = OssCleanupService()

    with patch("app.services.oss_cleanup_service.delete_file_from_oss_sync"):
        task = service.delete_file_after_commit_sync(
            file_path="avatars/old-pending.png",
            source="user.avatar",
        )

    assert task is not None
    assert pending_user.id is None
