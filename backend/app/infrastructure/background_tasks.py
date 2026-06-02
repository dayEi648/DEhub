import asyncio
import logging
from concurrent.futures import Future
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """应用级后台任务管理器。"""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def pending_count(self) -> int:
        return len(self._tasks)

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """绑定应用主事件循环，供线程安全调度后台任务。"""
        self._loop = loop

    def clear_loop(self) -> None:
        """清理已绑定的事件循环引用。"""
        self._loop = None

    def create_task(self, coroutine: Coroutine[Any, Any, Any], name: str) -> asyncio.Task:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None:
            task = loop.create_task(coroutine, name=name)
            return self._register_task(task)

        if self._loop is None or not self._loop.is_running():
            coroutine.close()
            raise RuntimeError("后台任务事件循环未初始化")

        scheduled: Future[asyncio.Task] = Future()

        def _schedule() -> None:
            try:
                task = self._loop.create_task(coroutine, name=name)
                scheduled.set_result(self._register_task(task))
            except Exception as exc:
                scheduled.set_exception(exc)

        self._loop.call_soon_threadsafe(_schedule)
        return scheduled.result(timeout=1)

    def _register_task(self, task: asyncio.Task) -> asyncio.Task:
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
