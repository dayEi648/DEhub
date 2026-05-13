from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graphs.chat_graph import (
    ChatState,
    _build_system_prompt,
    _require_owner,
)


class TestBuildSystemPrompt:
    """测试 System Prompt 与记忆拼接"""

    def test_no_memories(self):
        assert _build_system_prompt("原始提示", []) == "原始提示"

    def test_with_memories_and_original(self):
        result = _build_system_prompt("原始提示", ["[摘要] 用户喜欢Python"])
        assert "原始提示" in result
        assert "用户喜欢Python" in result
        assert "历史记忆" in result

    def test_with_memories_no_original(self):
        result = _build_system_prompt(None, ["[摘要] 用户喜欢Python"])
        assert "用户喜欢Python" in result
        assert "历史记忆" in result


class TestRequireOwner:
    """测试权限校验"""

    def test_owner_match(self):
        conv = MagicMock()
        conv.user_id = 1
        _require_owner(conv, 1)  # 不应抛异常

    def test_owner_mismatch(self):
        from fastapi import HTTPException

        conv = MagicMock()
        conv.user_id = 1
        with pytest.raises(HTTPException) as exc_info:
            _require_owner(conv, 2)
        assert exc_info.value.status_code == 403


class TestChatState:
    """测试 ChatState 数据结构"""

    def test_basic_state(self):
        state = ChatState(
            user_id=1,
            conversation_id=10,
            messages=[HumanMessage(content="hello")],
        )
        assert state["user_id"] == 1
        assert state["conversation_id"] == 10
        assert len(state["messages"]) == 1


class TestGraphCompile:
    """测试 Graph 编译"""

    def test_compile_success(self):
        from app.graphs import chat_graph as cg_module
        from app.graphs.chat_graph import build_chat_graph
        from app.infrastructure.langchain_adapter import CustomChatModel
        from app.infrastructure.llm_client import LLMClient

        # 清理缓存，确保每次测试都重新编译
        cg_module._graph_instance = None

        client = LLMClient(
            base_url="http://test",
            api_key="k",
            model="m",
            max_tokens=100,
            temperature=0.5,
            timeout=5,
        )
        llm = CustomChatModel(client)
        llm_small = CustomChatModel(client)

        graph = build_chat_graph(llm, llm_small)
        assert graph is not None

        # 测试缓存：第二次调用应返回同一个实例
        graph2 = build_chat_graph(llm, llm_small)
        assert graph2 is graph
