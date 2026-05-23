"""ToolRegistry 单元测试。"""

import pytest

from app.graphs.tool_registry import ToolMetadata, ToolRegistry, ToolRisk, ToolScope


class DummyTool:
    """辅助类，模拟 LangChain BaseTool 的最小接口。"""

    def __init__(self, name: str):
        self.name = name


class TestToolRegistry:
    """测试 ToolRegistry 核心功能。"""

    @staticmethod
    def _make_meta(name: str, scope: ToolScope = ToolScope.PUBLIC, risk: ToolRisk = ToolRisk.READONLY):
        return ToolMetadata(
            name=name,
            tool=DummyTool(name),
            risk=risk,
            scope=scope,
        )

    def test_register_and_list_all(self):
        """注册工具后应能通过 list_all 按名称排序返回。"""
        reg = ToolRegistry()
        meta_b = self._make_meta("tool_b")
        meta_a = self._make_meta("tool_a")

        reg.register(meta_b)
        reg.register(meta_a)

        all_tools = reg.list_all()
        assert len(all_tools) == 2
        assert [m.name for m in all_tools] == ["tool_a", "tool_b"]

    def test_register_duplicate_raises(self):
        """重复注册同名工具应抛出 ValueError。"""
        reg = ToolRegistry()
        reg.register(self._make_meta("dup"))
        with pytest.raises(ValueError, match="已注册"):
            reg.register(self._make_meta("dup"))

    def test_get_existing(self):
        """get 应返回已注册工具的元数据。"""
        reg = ToolRegistry()
        meta = self._make_meta("exists")
        reg.register(meta)
        assert reg.get("exists") == meta

    def test_get_missing_returns_none(self):
        """get 不存在的工具应返回 None。"""
        reg = ToolRegistry()
        assert reg.get("missing") is None

    # ------------------------------------------------------------------
    # resolve 权限过滤
    # ------------------------------------------------------------------

    def test_resolve_public_tools_for_all_levels(self):
        """PUBLIC 工具应对所有权限等级可见。"""
        reg = ToolRegistry()
        reg.register(self._make_meta("public_tool", scope=ToolScope.PUBLIC))

        for level in [0, 1, 2]:
            result = reg.resolve(permission_level=level)
            assert len(result) == 1
            assert result[0].name == "public_tool"

    def test_resolve_admin_tools_only_for_admin(self):
        """ADMIN 工具仅对 permission_level >= 1 可见。"""
        reg = ToolRegistry()
        reg.register(self._make_meta("user_tool", scope=ToolScope.PUBLIC))
        reg.register(self._make_meta("admin_tool", scope=ToolScope.ADMIN))

        # USER (level=0) 看不到 admin_tool
        user_tools = reg.resolve(permission_level=0)
        assert len(user_tools) == 1
        assert user_tools[0].name == "user_tool"

        # ADMIN (level=1) 和 SUPER_ADMIN (level=2) 都能看到
        for level in [1, 2]:
            tools = reg.resolve(permission_level=level)
            names = [t.name for t in tools]
            assert "user_tool" in names
            assert "admin_tool" in names

    def test_resolve_disabled_tools_hidden(self):
        """enabled=False 的工具不应出现在 resolve 结果中。"""
        reg = ToolRegistry()
        reg.register(
            ToolMetadata(
                name="enabled_tool",
                tool=DummyTool("enabled_tool"),
                risk=ToolRisk.READONLY,
                scope=ToolScope.PUBLIC,
                enabled=True,
            )
        )
        reg.register(
            ToolMetadata(
                name="disabled_tool",
                tool=DummyTool("disabled_tool"),
                risk=ToolRisk.READONLY,
                scope=ToolScope.PUBLIC,
                enabled=False,
            )
        )

        result = reg.resolve(permission_level=0)
        assert len(result) == 1
        assert result[0].name == "enabled_tool"

    def test_resolve_empty_registry(self):
        """空注册中心 resolve 应返回空列表。"""
        reg = ToolRegistry()
        assert reg.resolve(permission_level=0) == []

    def test_resolve_result_sorted(self):
        """resolve 返回的工具列表应按名称排序。"""
        reg = ToolRegistry()
        reg.register(self._make_meta("z_tool"))
        reg.register(self._make_meta("a_tool"))
        reg.register(self._make_meta("m_tool"))

        result = reg.resolve(permission_level=0)
        assert [t.name for t in result] == ["a_tool", "m_tool", "z_tool"]


class TestToolMetadata:
    """测试 ToolMetadata 的默认行为。"""

    def test_defaults(self):
        """未显式指定的字段应使用默认值。"""
        meta = ToolMetadata(
            name="test",
            tool=DummyTool("test"),
            risk=ToolRisk.READONLY,
            scope=ToolScope.PUBLIC,
        )
        assert meta.concurrency_safe is True
        assert meta.category == "general"
        assert meta.enabled is True

    def test_immutability(self):
        """frozen dataclass 应不可变。"""
        meta = ToolMetadata(
            name="test",
            tool=DummyTool("test"),
            risk=ToolRisk.READONLY,
            scope=ToolScope.PUBLIC,
        )
        with pytest.raises(AttributeError):
            meta.enabled = False
