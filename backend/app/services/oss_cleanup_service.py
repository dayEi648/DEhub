import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.oss_cleanup_task import OssCleanupTask
from app.storage.oss import delete_file_from_oss, delete_file_from_oss_sync

logger = logging.getLogger(__name__)


class OssCleanupService:
    """统一记录并执行 OSS 文件清理。"""

    _RETRY_DELAY_SECONDS = 300

    def __init__(self, db: Session):
        self.db = db

    def _create_task(self, file_path: str, source: str) -> OssCleanupTask:
        task = OssCleanupTask(file_path=file_path, source=source)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def _mark_succeeded(self, task: OssCleanupTask) -> OssCleanupTask:
        task.status = "succeeded"
        task.last_error = None
        task.next_retry_at = None
        self.db.commit()
        self.db.refresh(task)
        return task

    def _mark_failed(self, task: OssCleanupTask, exc: Exception) -> OssCleanupTask:
        task.status = "failed"
        task.retry_count += 1
        task.last_error = str(exc)
        task.next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=self._RETRY_DELAY_SECONDS
        )
        self.db.commit()
        self.db.refresh(task)
        return task

    async def delete_file_after_commit(
        self,
        file_path: str,
        source: str,
    ) -> OssCleanupTask:
        task = self._create_task(file_path=file_path, source=source)
        try:
            await delete_file_from_oss(file_path)
        except FileNotFoundError:
            return self._mark_succeeded(task)
        except Exception as exc:
            logger.exception("OSS 文件清理失败，已登记重试: file=%s", file_path)
            return self._mark_failed(task, exc)
        return self._mark_succeeded(task)

    def delete_file_after_commit_sync(
        self,
        file_path: str,
        source: str,
    ) -> OssCleanupTask:
        task = self._create_task(file_path=file_path, source=source)
        try:
            delete_file_from_oss_sync(file_path)
        except FileNotFoundError:
            return self._mark_succeeded(task)
        except Exception as exc:
            logger.exception("OSS 文件清理失败，已登记重试: file=%s", file_path)
            return self._mark_failed(task, exc)
        return self._mark_succeeded(task)
