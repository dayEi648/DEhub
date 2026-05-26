"""OpenAPI 管理员工具单元测试（阶段 5）。"""

from unittest.mock import MagicMock, patch

import pytest

from app.graphs.nodes.toolnodes import registry
from app.graphs.nodes.toolnodes.openapi_codegen import generate_openapi_call_example
from app.graphs.nodes.toolnodes.openapi_search import search_openapi_docs
from app.graphs.tool_registry import ToolScope


class TestToolRegistryAdmin:
    """测试 ToolRegistry 中 OpenAPI 工具的权限可见性。"""

    def test_user_does_not_see_openapi_tools(self):
        """普通用户（permission_level=0）不应看到 OpenAPI 工具。"""
        tools = registry.resolve(permission_level=0)
        names = [t.name for t in tools]
        assert "search_openapi_docs" not in names
        assert "generate_openapi_call_example" not in names

    def test_admin_sees_openapi_tools(self):
        """管理员（permission_level=1）应看到 OpenAPI 工具。"""
        tools = registry.resolve(permission_level=1)
        names = [t.name for t in tools]
        assert "search_openapi_docs" in names
        assert "generate_openapi_call_example" in names

    def test_super_admin_sees_openapi_tools(self):
        """超级管理员（permission_level=2）应看到 OpenAPI 工具。"""
        tools = registry.resolve(permission_level=2)
        names = [t.name for t in tools]
        assert "search_openapi_docs" in names
        assert "generate_openapi_call_example" in names

    def test_openapi_tools_are_admin_scope(self):
        """OpenAPI 工具的元数据应为 ADMIN 作用域。"""
        meta_search = registry.get("search_openapi_docs")
        assert meta_search is not None
        assert meta_search.scope == ToolScope.ADMIN

        meta_codegen = registry.get("generate_openapi_call_example")
        assert meta_codegen is not None
        assert meta_codegen.scope == ToolScope.ADMIN


class TestSearchOpenapiDocs:
    """测试 search_openapi_docs 工具。"""

    @patch("app.graphs.nodes.toolnodes.openapi_search.OpenAPIEmbeddingService")
    @patch("app.graphs.nodes.toolnodes.openapi_search.SessionLocal")
    def test_returns_formatted_results(self, mock_session_local, mock_service_cls):
        """有匹配文档时应返回格式化结果。"""
        mock_service = MagicMock()
        mock_service.search.return_value = [
            {
                "method": "GET",
                "path": "/users",
                "summary": "获取用户列表",
                "description": "分页获取所有用户",
                "operation_id": "listUsers",
                "tags": ["user"],
                "content": "GET /users\nSummary: 获取用户列表\n  - page (query, integer): 页码",
                "similarity_score": 0.95,
            }
        ]
        mock_service_cls.return_value = mock_service
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        result = search_openapi_docs.invoke({"query": "用户列表"})
        assert "GET /users" in result
        assert "获取用户列表" in result
        assert "0.9500" in result or "0.95" in result

    @patch("app.graphs.nodes.toolnodes.openapi_search.OpenAPIEmbeddingService")
    @patch("app.graphs.nodes.toolnodes.openapi_search.SessionLocal")
    def test_no_results_returns_clear_message(self, mock_session_local, mock_service_cls):
        """无匹配文档时应明确说明。"""
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service_cls.return_value = mock_service
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        result = search_openapi_docs.invoke({"query": "不存在的接口"})
        assert "当前知识库未找到相关接口" in result

    def test_empty_query_returns_prompt(self):
        """空查询应返回提示。"""
        result = search_openapi_docs.invoke({"query": ""})
        assert "未提供有效的搜索关键词" in result


class TestGenerateOpenapiCallExample:
    """测试 generate_openapi_call_example 工具。"""

    @patch("app.graphs.nodes.toolnodes.openapi_codegen.OpenAPIEmbeddingService")
    @patch("app.graphs.nodes.toolnodes.openapi_codegen.SessionLocal")
    def test_returns_example_structure(self, mock_session_local, mock_service_cls):
        """有匹配文档时应返回调用示例结构。"""
        mock_service = MagicMock()
        mock_service.search.return_value = [
            {
                "method": "POST",
                "path": "/auth/login",
                "summary": "用户登录",
                "content": "POST /auth/login\nSummary: 用户登录\nRequest Body (application/json):\n  - username (string): 用户名\n  - password (string): 密码\nResponse 200: 登录成功",
                "similarity_score": 0.92,
            }
        ]
        mock_service_cls.return_value = mock_service
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        result = generate_openapi_call_example.invoke({"query": "登录接口示例"})
        assert "POST /auth/login" in result
        assert "用户登录" in result
        assert "基于知识库中的以下接口" in result

    @patch("app.graphs.nodes.toolnodes.openapi_codegen.OpenAPIEmbeddingService")
    @patch("app.graphs.nodes.toolnodes.openapi_codegen.SessionLocal")
    def test_no_results_returns_clear_message(self, mock_session_local, mock_service_cls):
        """无匹配文档时应明确说明无法生成示例。"""
        mock_service = MagicMock()
        mock_service.search.return_value = []
        mock_service_cls.return_value = mock_service
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db

        result = generate_openapi_call_example.invoke({"query": "不存在的接口"})
        assert "当前知识库未找到相关接口，无法生成示例" in result

    def test_empty_query_returns_prompt(self):
        """空查询应返回提示。"""
        result = generate_openapi_call_example.invoke({"query": ""})
        assert "未提供有效的搜索关键词" in result
