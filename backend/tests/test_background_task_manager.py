import asyncio

import pytest

from app.infrastructure.background_tasks import BackgroundTaskManager


@pytest.mark.asyncio
async def test_background_task_manager_tracks_and_removes_completed_tasks():
    manager = BackgroundTaskManager()

    async def work() -> None:
        await asyncio.sleep(0)

    manager.create_task(work(), name="unit.work")
    assert manager.pending_count == 1

    await manager.shutdown(timeout=1)

    assert manager.pending_count == 0


@pytest.mark.asyncio
async def test_background_task_manager_records_task_exceptions(caplog):
    manager = BackgroundTaskManager()

    async def fail() -> None:
        raise RuntimeError("background failed")

    manager.create_task(fail(), name="unit.fail")
    await manager.shutdown(timeout=1)

    assert manager.pending_count == 0
    assert "后台任务失败: unit.fail" in caplog.text


@pytest.mark.asyncio
async def test_background_task_manager_cancels_tasks_on_shutdown_timeout():
    manager = BackgroundTaskManager()

    async def wait_forever() -> None:
        await asyncio.sleep(60)

    task = manager.create_task(wait_forever(), name="unit.timeout")
    await manager.shutdown(timeout=0.01)

    assert task.cancelled()
    assert manager.pending_count == 0
