"""工具治理层：元数据定义与注册中心。

在 LangChain @tool（接口层）之上提供运行时治理：
- 工具元数据（风险等级、作用域、并发安全性）
- 按用户权限动态过滤可用工具
- 全局注册与发现
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from langchain_core.tools import BaseTool


class ToolRisk(Enum):
    """工具风险等级，用于执行策略决策。"""

    READONLY = "readonly"
    """只读操作，可安全并发执行。"""
    IDEMPOTENT = "idempotent"
    """幂等操作，重复执行结果不变，如设置状态、更新记录。"""
    DESTRUCTIVE = "destructive"
    """不可逆操作，如删除、覆盖，执行前可能需要人工确认。"""


class ToolScope(Enum):
    """工具可见性作用域，用于权限过滤。"""

    PUBLIC = "public"
    """无额外权限门槛，所有已登录用户均可用。"""
    AUTHENTICATED = "authenticated"
    """需要登录用户身份（语义上区别于 PUBLIC，当前阶段效果相同）。"""
    ADMIN = "admin"
    """仅管理员及以上可用。"""


@dataclass(frozen=True, slots=True)
class ToolMetadata:
    """应用层工具元数据封装。

    在 LangChain BaseTool 之上附加运行时治理所需的属性，
    本身不可变，确保注册后元数据不会被意外修改。
    """

    name: str
    """工具唯一标识名（与 LLM 看到的 tool name 一致）。"""
    tool: BaseTool
    """由 @tool 或 StructuredTool 生成的 LangChain 工具实例。"""
    risk: ToolRisk
    """风险等级，决定执行策略。"""
    scope: ToolScope
    """可见性作用域，决定哪些用户能看到该工具。"""
    concurrency_safe: bool = True
    """同一用户的多个 tool_calls 能否并发执行。"""
    category: str = "general"
    """工具分类标签，用于未来按场景动态裁剪。"""
    enabled: bool = True
    """是否启用，支持 Feature Flag 灰度开关。"""


class ToolRegistry:
    """工具注册中心。

    线程安全模型：注册发生在模块导入阶段（单线程），
    运行时 resolve/list_all/get 均为只读操作，无需额外锁。
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolMetadata] = {}

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------

    def register(self, meta: ToolMetadata) -> None:
        """注册工具元数据。

        Args:
            meta: 工具元数据实例。

        Raises:
            ValueError: 同一 name 重复注册。
        """
        if meta.name in self._tools:
            raise ValueError(f"工具 '{meta.name}' 已注册")
        self._tools[meta.name] = meta

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get(self, name: str) -> ToolMetadata | None:
        """按名称获取工具元数据。"""
        return self._tools.get(name)

    def list_all(self) -> list[ToolMetadata]:
        """返回所有已注册工具的元数据列表（按名称排序）。"""
        return [self._tools[name] for name in sorted(self._tools)]

    # ------------------------------------------------------------------
    # 动态解析（核心：按权限过滤可用工具）
    # ------------------------------------------------------------------

    def resolve(self, permission_level: int = 0) -> list[BaseTool]:
        """根据用户权限等级解析当前可用的工具列表。

        过滤规则：
        - 未启用的工具（enabled=False）不可见
        - ADMIN 级别工具仅当 permission_level >= 1 时可见
        - PUBLIC / AUTHENTICATED 工具对当前所有已登录用户均可见
          （因为当前 AI 对话接口均要求登录）

        Args:
            permission_level: 用户权限等级，对应 PermissionLevel 的整数值。
                              0=USER, 1=ADMIN, 2=SUPER_ADMIN。

        Returns:
            可用于 `model.bind_tools()` 的 BaseTool 实例列表（按名称排序）。
        """
        result: list[BaseTool] = []
        for meta in sorted(self._tools.values(), key=lambda m: m.name):
            if not meta.enabled:
                continue
            if meta.scope == ToolScope.ADMIN and permission_level < 1:
                continue
            result.append(meta.tool)
        return result
