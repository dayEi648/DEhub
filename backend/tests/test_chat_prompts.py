"""chat_prompts 单元测试。"""

from datetime import datetime

import pytest

from app.prompts.chat_prompts import (
    CHAT_FIXED_SYSTEM_PROMPT,
    render_chat_system_prompt,
    render_current_goal_prompt,
)


class TestRenderChatSystemPrompt:
    """测试 render_chat_system_prompt 渲染逻辑。"""

    def test_returns_only_fixed_when_no_dynamic_fields(self):
        """所有动态字段为空时，应只返回固定 prompt。"""
        result = render_chat_system_prompt()
        assert result == CHAT_FIXED_SYSTEM_PROMPT
        assert "<dynamic_context>" not in result

    def test_includes_current_time(self):
        """传入 current_time 时应渲染时间段落。"""
        result = render_chat_system_prompt(current_time="2026-05-24 14:30")
        assert "当前时间：2026-05-24 14:30" in result
        assert "<dynamic_context>" in result

    def test_includes_scene(self):
        """传入 scene 时应渲染场景段落。"""
        result = render_chat_system_prompt(scene="对话开始")
        assert "当前场景：对话开始" in result

    def test_includes_profile_text(self):
        """传入 profile_text 时应渲染用户画像段落。"""
        result = render_chat_system_prompt(profile_text="用户是 Python 开发者")
        assert "--- 用户画像 ---" in result
        assert "用户是 Python 开发者" in result

    def test_includes_current_goal(self):
        """传入 current_goal 时应渲染目标段落。"""
        result = render_chat_system_prompt(current_goal="了解 Docker 部署流程")
        assert "当前目标：了解 Docker 部署流程" in result

    def test_omits_empty_fields(self):
        """空字段不应在结果中渲染对应段落。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            scene="持续对话",
            profile_text=None,
            current_goal="",
        )
        assert "当前时间：" in result
        assert "当前场景：持续对话" in result
        assert "--- 用户画像 ---" not in result
        assert "当前目标：" not in result

    def test_all_fields_together(self):
        """所有字段同时存在时应完整渲染。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            scene="工具结果返回后继续回答",
            profile_text="用户是前端开发者",
            current_goal="学习 React 19 新特性",
        )
        assert CHAT_FIXED_SYSTEM_PROMPT in result
        assert "当前时间：2026-05-24 14:30" in result
        assert "当前场景：工具结果返回后继续回答" in result
        assert "用户是前端开发者" in result
        assert "当前目标：学习 React 19 新特性" in result

    # ------------------------------------------------------------------
    # permission_level OpenAPI 权限注入
    # ------------------------------------------------------------------

    def test_user_prompt_no_openapi_capability(self):
        """普通用户（permission_level=0）Prompt 不应包含 OpenAPI 能力描述。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            permission_level=0,
        )
        assert "OpenAPI" not in result
        assert "知识库" not in result
        assert "admin_capabilities" not in result

    def test_user_prompt_none_permission_no_openapi(self):
        """permission_level=None 时 Prompt 不应包含 OpenAPI 能力描述。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            permission_level=None,
        )
        assert "OpenAPI" not in result
        assert "知识库" not in result
        assert "admin_capabilities" not in result

    def test_admin_prompt_includes_openapi_capability(self):
        """管理员（permission_level=1）Prompt 应包含 OpenAPI 能力描述。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            permission_level=1,
        )
        assert "admin_capabilities" in result
        assert "OpenAPI 文档知识库" in result
        assert "当前知识库未找到相关接口" in result

    def test_super_admin_prompt_includes_openapi_capability(self):
        """超级管理员（permission_level=2）Prompt 应包含 OpenAPI 能力描述。"""
        result = render_chat_system_prompt(
            current_time="2026-05-24 14:30",
            permission_level=2,
        )
        assert "admin_capabilities" in result
        assert "OpenAPI 文档知识库" in result


class TestRenderCurrentGoalPrompt:
    """测试 render_current_goal_prompt 渲染逻辑。"""

    def test_without_previous_goal(self):
        """无历史目标时不应渲染历史目标段落。"""
        result = render_current_goal_prompt(conversation="用户：你好\n助手：你好")
        assert "历史目标：" not in result
        assert "对话内容：\n用户：你好\n助手：你好" in result

    def test_with_previous_goal(self):
        """有历史目标时应渲染历史目标段落。"""
        result = render_current_goal_prompt(
            conversation="用户：你好",
            previous_goal="了解 Docker",
        )
        assert "历史目标：了解 Docker" in result
        assert "对话内容：\n用户：你好" in result
