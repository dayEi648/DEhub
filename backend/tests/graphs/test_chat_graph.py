"""Chat Graph 节点单元测试。"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.graph import END

from app.graphs.nodes.chat.agent import (
    _filter_system_messages,
    _resolve_scene,
    agent_node,
)
from app.graphs.nodes.chat.router import route_after_agent
from app.graphs.nodes.chat.tool_executor import tool_executor_node
from app.graphs.states.chat_state import ChatState


# ===================================================================
# _filter_system_messages
# ===================================================================

class TestFilterSystemMessages:
    def test_filters_out_system_messages(self):
        messages = [
            SystemMessage(content="sys"),
            HumanMessage(content="hi"),
            SystemMessage(content="sys2"),
            AIMessage(content="hello"),
        ]
        result = _filter_system_messages(messages)
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)

    def test_empty_list(self):
        assert _filter_system_messages([]) == []


# ===================================================================
# _resolve_scene
# ===================================================================

class TestResolveScene:
    def test_returns_prompt_scene_when_no_tool_message(self):
        state = ChatState(
            messages=[HumanMessage(content="hi")],
            prompt_scene="对话开始",
        )
        assert _resolve_scene(state) == "对话开始"

    def test_returns_tool_scene_when_last_is_tool_message(self):
        state = ChatState(
            messages=[
                HumanMessage(content="hi"),
                AIMessage(content="", tool_calls=[{"name": "search_blog", "args": {}, "id": "call_1"}]),
                ToolMessage(content="result", tool_call_id="call_1", name="search_blog"),
            ],
            prompt_scene="持续对话",
        )
        assert _resolve_scene(state) == "工具结果返回后继续回答"


# ===================================================================
# route_after_agent
# ===================================================================

class TestRouteAfterAgent:
    def test_route_to_tools_when_tool_calls_present(self):
        state = ChatState(
            messages=[
                HumanMessage(content="hi"),
                AIMessage(content="", tool_calls=[{"name": "search_blog", "args": {}, "id": "call_1"}]),
            ]
        )
        assert route_after_agent(state) == "tool_executor"

    def test_route_to_end_when_no_tool_calls(self):
        state = ChatState(
            messages=[
                HumanMessage(content="hi"),
                AIMessage(content="Hello!"),
            ]
        )
        assert route_after_agent(state) == END

    def test_route_to_end_when_empty_messages(self):
        state = ChatState(messages=[])
        assert route_after_agent(state) == END


# ===================================================================
# tool_executor_node
# ===================================================================

class TestToolExecutorNode:
    @pytest.mark.asyncio
    async def test_empty_messages_returns_empty(self):
        state = ChatState(messages=[])
        result = await tool_executor_node(state)
        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_no_tool_calls_returns_empty(self):
        state = ChatState(
            messages=[
                HumanMessage(content="hi"),
                AIMessage(content="Hello!"),
            ]
        )
        result = await tool_executor_node(state)
        assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_executes_tool_and_returns_tool_message(self):
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = "blog result"

        mock_meta = MagicMock()
        mock_meta.concurrency_safe = True
        mock_meta.tool = mock_tool

        with patch(
            "app.graphs.nodes.chat.tool_executor.registry.get",
            return_value=mock_meta,
        ):
            state = ChatState(
                messages=[
                    HumanMessage(content="hi"),
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "search_blog",
                                "args": {"query": "docker"},
                                "id": "call_1",
                            }
                        ],
                    ),
                ]
            )
            result = await tool_executor_node(state)
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], ToolMessage)
            assert result["messages"][0].content == "blog result"
            assert result["messages"][0].tool_call_id == "call_1"

    @pytest.mark.asyncio
    async def test_unregistered_tool_returns_error_tool_message(self):
        with patch(
            "app.graphs.nodes.chat.tool_executor.registry.get",
            return_value=None,
        ):
            state = ChatState(
                messages=[
                    HumanMessage(content="hi"),
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "unknown_tool",
                                "args": {},
                                "id": "call_1",
                            }
                        ],
                    ),
                ]
            )
            result = await tool_executor_node(state)
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], ToolMessage)
            assert "未注册工具" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_tool_exception_wrapped_as_tool_message(self):
        mock_tool = MagicMock()
        mock_tool.invoke.side_effect = RuntimeError("network error")

        mock_meta = MagicMock()
        mock_meta.concurrency_safe = True
        mock_meta.tool = mock_tool

        with patch(
            "app.graphs.nodes.chat.tool_executor.registry.get",
            return_value=mock_meta,
        ):
            state = ChatState(
                messages=[
                    HumanMessage(content="hi"),
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "search_blog",
                                "args": {"query": "docker"},
                                "id": "call_1",
                            }
                        ],
                    ),
                ]
            )
            result = await tool_executor_node(state)
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], ToolMessage)
            assert "Error: network error" in result["messages"][0].content

    @pytest.mark.asyncio
    async def test_safe_tools_run_in_parallel(self):
        call_order = []

        def make_mock_tool(name: str, delay: float):
            mock_tool = MagicMock()

            def side_effect(*args, **kwargs):
                call_order.append(name)
                return f"{name} result"

            mock_tool.invoke.side_effect = side_effect
            return mock_tool

        mock_meta_blog = MagicMock()
        mock_meta_blog.concurrency_safe = True
        mock_meta_blog.tool = make_mock_tool("search_blog", 0.1)

        mock_meta_web = MagicMock()
        mock_meta_web.concurrency_safe = True
        mock_meta_web.tool = make_mock_tool("search_web", 0.1)

        def mock_get(name):
            if name == "search_blog":
                return mock_meta_blog
            if name == "search_web":
                return mock_meta_web
            return None

        with patch(
            "app.graphs.nodes.chat.tool_executor.registry.get",
            side_effect=mock_get,
        ):
            state = ChatState(
                messages=[
                    HumanMessage(content="hi"),
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "search_blog",
                                "args": {"query": "docker"},
                                "id": "call_1",
                            },
                            {
                                "name": "search_web",
                                "args": {"query": "news"},
                                "id": "call_2",
                            },
                        ],
                    ),
                ]
            )
            result = await tool_executor_node(state)
            assert len(result["messages"]) == 2
            # 并行执行时，两个工具应该都被调用
            assert "search_blog" in call_order
            assert "search_web" in call_order


# ===================================================================
# agent_node (integration-level mocks)
# ===================================================================

class TestAgentNode:
    @pytest.mark.asyncio
    async def test_agent_node_returns_aimessage(self):
        mock_response = AIMessage(content="Hello!")
        mock_model = AsyncMock()
        mock_model.ainvoke.return_value = mock_response

        with patch(
            "app.graphs.nodes.chat.agent._get_bound_model",
            return_value=mock_model,
        ):
            state = ChatState(
                messages=[HumanMessage(content="hi")],
                permission_level=0,
                prompt_scene="对话开始",
            )
            result = await agent_node(state, {"configurable": {"thread_id": "1"}})
            assert len(result["messages"]) == 1
            assert isinstance(result["messages"][0], AIMessage)
            assert result["messages"][0].content == "Hello!"

            # 验证传给 LLM 的消息列表包含 SystemMessage
            call_args = mock_model.ainvoke.call_args
            messages_passed = call_args[0][0]
            assert isinstance(messages_passed[0], SystemMessage)
            assert isinstance(messages_passed[1], HumanMessage)
