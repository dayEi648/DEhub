from enum import IntEnum


class PermissionLevel(IntEnum):
    """用户权限等级。"""

    USER = 0
    ADMIN = 1
    SUPER_ADMIN = 2

