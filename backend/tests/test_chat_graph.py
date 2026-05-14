from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graphs.chat_graph import (
    ChatState,
    _build_system_prompt,
    _format_blog_knowledge,
    _require_owner,
    _should_continue,
    _build_tools_node,
)


class TestFormatBlogKnowledge:
    """测试博客知识格式化逻辑"""

    def test_empty_results(self):
        assert _format_blog_knowledge([]) == []

    def test_with_summary(self):
        result = MagicMock()
        result.title = "FastAPI 入门"
        result.slug = "fastapi-ru-men"
        result.summary = "这是一篇关于 FastAPI 的教程"
        formatted = _format_blog_knowledge([result])
        assert len(formatted) == 1
        assert "[博客文章]" in formatted[0]
        assert "FastAPI 入门" in formatted[0]
        assert "这是一篇关于 FastAPI 的教程" in formatted[0]
        assert "链接：/blog/fastapi-ru-men" in formatted[0]

    def test_without_summary(self):
        result = MagicMock()
        result.title = "Python 技巧"
        result.slug = "python-ji-qiao"
        result.summary = None
        formatted = _format_blog_knowledge([result])
        assert len(formatted) == 1
        assert "[博客文章] Python 技巧" in formatted[0]
        assert "链接：/blog/python-ji-qiao" in formatted[0]


class TestBuildSystemPrompt:
    """测试 System Prompt 与记忆拼接（仅使用后端既定 DEFAULT_SYSTEM）"""

    def test_no_memories(self):
        result = _build_system_prompt([])
        assert "DE Hub" in result  # 默认角色设定
        assert "禁止" in result  # 安全约束应被追加

    def test_with_memories(self):
        result = _build_system_prompt(["[摘要] 用户喜欢Python"])
        assert "DE Hub" in result  # 默认角色设定
        assert "用户喜欢Python" in result
        assert "历史记忆" in result
        assert "禁止" in result  # 安全约束应被追加


class TestShouldContinue:
    """测试条件边路由逻辑"""

    def test_no_messages(self):
        state = {"messages": []}
        assert _should_continue(state) == "persist"

    def test_normal_ai_message(self):
        state = {"messages": [AIMessage(content="你好")]}
        assert _should_continue(state) == "persist"

    def test_ai_message_with_tool_calls(self):
        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{"name": "search_blog", "args": {"query": "test"}, "id": "call_1"}],
                )
            ]
        }
        assert _should_continue(state) == "tools"


class TestToolsNode:
    """测试工具执行节点"""

    @pytest.mark.asyncio
    async def test_no_tool_calls(self):
        node = _build_tools_node()
        state = {"messages": [AIMessage(content="你好")]}
        config = {"configurable": {"db": MagicMock()}}
        result = await node(state, config)
        assert result == {}

    @pytest.mark.asyncio
    async def test_search_blog_tool_call(self):
        node = _build_tools_node()
        state = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[{"name": "search_blog", "args": {"query": "FastAPI"}, "id": "call_1"}],
                )
            ]
        }
        config = {"configurable": {"db": MagicMock()}}

        mock_result = MagicMock()
        mock_result.title = "FastAPI 教程"
        mock_result.slug = "fastapi-jiao-cheng"
        mock_result.summary = "入门指南"

        with patch(
            "app.graphs.chat_graph.BlogVectorSearchService.search",
            new_callable=AsyncMock,
            return_value=[mock_result],
        ):
            result = await node(state, config)
            msgs = result.get("messages", [])
            assert len(msgs) == 1
            assert "[博客文章] FastAPI 教程" in msgs[0].content
            assert "链接：/blog/fastapi-jiao-cheng" in msgs[0].content
            assert "入门指南" in msgs[0].content
            assert msgs[0].tool_call_id == "call_1"


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
    """测试 Graph 编译与缓存"""

    def test_compile_success(self):
        from app.graphs.chat_graph import build_chat_graph, invalidate_graph_cache

        # 清理缓存，确保每次测试都重新编译
        invalidate_graph_cache()

        llm = MagicMock()
        llm.model_name = "m"
        llm_small = MagicMock()
        llm_small.model_name = "m"

        graph = build_chat_graph(llm, llm_small)
        assert graph is not None

        # 测试缓存：相同模型配置第二次调用应返回同一个实例
        graph2 = build_chat_graph(llm, llm_small)
        assert graph2 is graph

    def test_cache_by_model_config(self):
        """不同模型配置应生成不同的缓存实例"""
        from app.graphs.chat_graph import build_chat_graph, invalidate_graph_cache

        invalidate_graph_cache()

        llm_a = MagicMock()
        llm_a.model_name = "model-a"
        llm_b = MagicMock()
        llm_b.model_name = "model-b"

        graph_a = build_chat_graph(llm_a, llm_a)
        graph_b = build_chat_graph(llm_b, llm_b)

        assert graph_a is not graph_b

        # 相同模型配置再次调用应命中缓存
        graph_a2 = build_chat_graph(llm_a, llm_a)
        assert graph_a2 is graph_a


class TestStreamChatInternal:
    """测试 ChatGraphService.stream_chat 内部逻辑（不经过 HTTP 层）"""

    @pytest.fixture
    def mock_service(self):
        from app.services.chat_graph_service import ChatGraphService

        mock_db = MagicMock()
        mock_llm = MagicMock()
        mock_llm.model_name = "test-model"

        with patch(
            "app.infrastructure.redis_checkpoint.get_redis_client", return_value=MagicMock()
        ), patch(
            "app.services.chat_graph_service.get_llm_client", return_value=mock_llm
        ), patch(
            "app.services.chat_graph_service.get_llm_small_client", return_value=mock_llm
        ):
            service = ChatGraphService(mock_db)

        # 替换 graph 避免真实编译
        service._graph = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_loads_history_for_existing_conversation(self, mock_service):
        """已有对话时，stream_chat 应从数据库加载历史消息注入 initial_state"""
        mock_msg1 = MagicMock()
        mock_msg1.role = "user"
        mock_msg1.content = "之前的问题"
        mock_msg2 = MagicMock()
        mock_msg2.role = "assistant"
        mock_msg2.content = "之前的回答"

        captured_state = None

        async def mock_astream_events(initial_state, config, version):
            nonlocal captured_state
            captured_state = initial_state
            if False:
                yield {}

        mock_service._graph.astream_events = mock_astream_events

        with patch(
            "app.crud.conversation_message.list_conversation_messages",
            return_value=[mock_msg1, mock_msg2],
        ):
            async for _ in mock_service.stream_chat(
                user_id=1, conversation_id=10, content="当前问题"
            ):
                pass

        assert captured_state is not None
        messages = captured_state["messages"]
        assert len(messages) == 3
        assert messages[0].content == "之前的问题"
        assert messages[1].content == "之前的回答"
        assert messages[2].content == "当前问题"

    @pytest.mark.asyncio
    async def test_new_conversation_unique_thread_id(self, mock_service):
        """新对话时应生成唯一的临时 thread_id，避免并发冲突"""
        captured_configs = []

        async def mock_astream_events(initial_state, config, version):
            captured_configs.append(config)
            if False:
                yield {}

        mock_service._graph.astream_events = mock_astream_events

        async for _ in mock_service.stream_chat(
            user_id=1, conversation_id=None, content="hi1"
        ):
            pass

        async for _ in mock_service.stream_chat(
            user_id=1, conversation_id=None, content="hi2"
        ):
            pass

        thread_id_1 = captured_configs[0]["configurable"]["thread_id"]
        thread_id_2 = captured_configs[1]["configurable"]["thread_id"]

        assert thread_id_1 != thread_id_2
        assert thread_id_1.startswith("new-")
        assert thread_id_2.startswith("new-")
