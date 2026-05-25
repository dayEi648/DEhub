import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.oss_cleanup_task import OssCleanupTask
from app.storage.oss import delete_file_from_oss, delete_file_from_oss_sync

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]


class OssCleanupService:
    """
    统一记录并执行 OSS 文件清理。

    清理任务使用独立数据库会话提交，避免提交调用方业务事务中的未提交变更。
    """

    _RETRY_DELAY_SECONDS = 300

    def __init__(
        self,
        session_factory: SessionFactory = SessionLocal,
    ):
        """
        Args:
            session_factory: 清理任务专用会话工厂。
        """
        self._session_factory = session_factory

    def _rollback_safely(self, db: Session) -> None:
        try:
            db.rollback()
        except Exception:
            logger.exception("OSS 清理任务数据库会话回滚失败")

    def _create_task(self, file_path: str, source: str) -> OssCleanupTask:
        db = self._session_factory()
        try:
            task = OssCleanupTask(file_path=file_path, source=source)
            db.add(task)
            db.commit()
            db.refresh(task)
            db.expunge(task)
            return task
        except Exception:
            self._rollback_safely(db)
            raise
        finally:
            db.close()

    def _mark_succeeded(self, task: OssCleanupTask) -> OssCleanupTask:
        db = self._session_factory()
        try:
            db_task = db.get(OssCleanupTask, task.id)
            if db_task is None:
                raise RuntimeError(f"OSS 清理任务不存在: id={task.id}")
            db_task.status = "succeeded"
            db_task.last_error = None
            db_task.next_retry_at = None
            db.commit()
            db.refresh(db_task)
            db.expunge(db_task)
            return db_task
        except Exception:
            self._rollback_safely(db)
            raise
        finally:
            db.close()

    def _mark_failed(self, task: OssCleanupTask, exc: Exception) -> OssCleanupTask:
        db = self._session_factory()
        try:
            db_task = db.get(OssCleanupTask, task.id)
            if db_task is None:
                raise RuntimeError(f"OSS 清理任务不存在: id={task.id}")
            db_task.status = "failed"
            db_task.retry_count += 1
            db_task.last_error = str(exc)
            db_task.next_retry_at = datetime.now(timezone.utc) + timedelta(
                seconds=self._RETRY_DELAY_SECONDS
            )
            db.commit()
            db.refresh(db_task)
            db.expunge(db_task)
            return db_task
        except Exception:
            self._rollback_safely(db)
            raise
        finally:
            db.close()

    def _mark_succeeded_safely(
        self,
        task: OssCleanupTask,
        file_path: str,
        source: str,
    ) -> OssCleanupTask | None:
        try:
            return self._mark_succeeded(task)
        except Exception:
            logger.exception(
                "OSS 清理任务标记成功失败: file=%s, source=%s",
                file_path,
                source,
            )
            return None

    def _mark_failed_safely(
        self,
        task: OssCleanupTask,
        exc: Exception,
        file_path: str,
        source: str,
    ) -> OssCleanupTask | None:
        try:
            return self._mark_failed(task, exc)
        except Exception:
            logger.exception(
                "OSS 清理任务标记失败状态失败: file=%s, source=%s",
                file_path,
                source,
            )
            return None

    async def delete_file_after_commit(
        self,
        file_path: str,
        source: str,
    ) -> OssCleanupTask | None:
        try:
            task = await asyncio.to_thread(self._create_task, file_path, source)
        except Exception:
            logger.exception(
                "OSS 清理任务创建失败，跳过持久化: file=%s, source=%s",
                file_path,
                source,
            )
            return None

        try:
            await delete_file_from_oss(file_path)
        except FileNotFoundError:
            return await asyncio.to_thread(
                self._mark_succeeded_safely, task, file_path, source
            )
        except Exception as exc:
            logger.exception("OSS 文件清理失败，已登记重试: file=%s", file_path)
            return await asyncio.to_thread(
                self._mark_failed_safely, task, exc, file_path, source
            )
        return await asyncio.to_thread(
            self._mark_succeeded_safely, task, file_path, source
        )

    def delete_file_after_commit_sync(
        self,
        file_path: str,
        source: str,
    ) -> OssCleanupTask | None:
        try:
            task = self._create_task(file_path=file_path, source=source)
        except Exception:
            logger.exception(
                "OSS 清理任务创建失败，跳过持久化: file=%s, source=%s",
                file_path,
                source,
            )
            return None

        try:
            delete_file_from_oss_sync(file_path)
        except FileNotFoundError:
            return self._mark_succeeded_safely(task, file_path, source)
        except Exception as exc:
            logger.exception("OSS 文件清理失败，已登记重试: file=%s", file_path)
            return self._mark_failed_safely(task, exc, file_path, source)
        return self._mark_succeeded_safely(task, file_path, source)
