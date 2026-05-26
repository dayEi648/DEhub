from datetime import datetime

from sqlalchemy.orm import Session

from app.crud import system_log as system_log_crud
from app.models.system_log import SystemLog


class SystemLogService:
    def __init__(self, db: Session):
        self.db = db

    def list_logs(
        self,
        skip: int = 0,
        limit: int = 20,
        level: str | None = None,
        is_resolved: bool | None = None,
        module: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
    ) -> tuple[list[SystemLog], int]:
        return system_log_crud.get_logs(
            self.db,
            skip=skip,
            limit=limit,
            level=level,
            is_resolved=is_resolved,
            module=module,
            created_after=created_after,
            created_before=created_before,
        )

    def get_stats(self) -> dict[str, int]:
        return system_log_crud.get_stats(self.db)

    def batch_resolve_logs(self, log_ids: list[int], resolved_by: int) -> int:
        return system_log_crud.batch_resolve_logs(
            self.db, log_ids, resolved_by=resolved_by
        )

    def get_log(self, log_id: int) -> SystemLog | None:
        return system_log_crud.get_log_by_id(self.db, log_id)

    def resolve_log(self, log_id: int, resolved_by: int) -> SystemLog | None:
        return system_log_crud.resolve_log(self.db, log_id, resolved_by=resolved_by)

    def delete_log(self, log_id: int) -> bool:
        return system_log_crud.delete_log(self.db, log_id)
