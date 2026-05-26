from unittest.mock import MagicMock, patch

from app.api.v1 import system_logs
from app.schemas.system_log import SystemLogListResponse


def test_list_system_logs_delegates_to_service():
    db = MagicMock()
    current_user = MagicMock()

    with (
        patch.object(system_logs, "require_admin") as mock_require_admin,
        patch.object(system_logs, "SystemLogService") as mock_service_cls,
    ):
        service = mock_service_cls.return_value
        service.list_logs.return_value = ([], 0)

        result = system_logs.list_system_logs(
            skip=0,
            limit=20,
            level=None,
            is_resolved=None,
            module=None,
            created_after=None,
            created_before=None,
            db=db,
            current_user=current_user,
        )

    mock_require_admin.assert_called_once_with(current_user)
    mock_service_cls.assert_called_once_with(db)
    service.list_logs.assert_called_once_with(
        skip=0,
        limit=20,
        level=None,
        is_resolved=None,
        module=None,
        created_after=None,
        created_before=None,
    )
    assert result == SystemLogListResponse(items=[], total=0)
