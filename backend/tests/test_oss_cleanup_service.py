from unittest.mock import AsyncMock, patch

import pytest

from app.models.oss_cleanup_task import OssCleanupTask
from app.services.oss_cleanup_service import OssCleanupService


@pytest.mark.asyncio
async def test_async_cleanup_failure_is_persisted_for_retry(db_session):
    service = OssCleanupService(db_session)

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
    service = OssCleanupService(db_session)

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
    service = OssCleanupService(db_session)

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
