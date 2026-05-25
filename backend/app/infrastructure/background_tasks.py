import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """应用级后台任务管理器。"""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    @property
    def pending_count(self) -> int:
        return len(self._tasks)

    def create_task(self, coroutine: Coroutine[Any, Any, Any], name: str) -> asyncio.Task:
        task = asyncio.create_task(coroutine, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._handle_done)
        return task

    def _handle_done(self, task: asyncio.Task) -> None:
        if task not in self._tasks:
            return
        self._tasks.discard(task)
        if task.cancelled():
            logger.warning("后台任务已取消: %s", task.get_name())
            return
        try:
            task.result()
        except Exception:
            logger.exception("后台任务失败: %s", task.get_name())

    async def shutdown(self, timeout: float = 10.0) -> None:
        if not self._tasks:
            return

        done, pending = await asyncio.wait(self._tasks, timeout=timeout)
        for task in done:
            self._handle_done(task)

        if not pending:
            return

        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in list(pending):
            self._handle_done(task)


background_task_manager = BackgroundTaskManager()
