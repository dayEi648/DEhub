"""Tool 节点共享上下文变量。

供 tool_executor_node 注入当前用户身份，
供各 tool 实现内部读取，避免循环导入。
"""

import contextvars

current_user_id_var: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "current_user_id", default=None
)
