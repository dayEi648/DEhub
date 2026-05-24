"""chat_service 单元测试。"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from langchain_core.messages import AIMessage, HumanMessage

from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService


class TestChatServiceChat:
    """测试 ChatService.chat() 方法。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph") as mock_get_graph:
            mock_get_graph.return_value = MagicMock()
            self.service = ChatService(self.mock_db)
            self.service.graph = MagicMock()
            self.service.graph.aget_state = AsyncMock(return_value=None)

    @patch("app.services.chat_service.conv_crud.create_ai_conversation")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    @patch.object(ChatService, "_ensure_title_async")
    @patch.object(ChatService, "_maybe_update_profile_async")
    async def test_chat_creates_new_conversation_when_no_id(
        self, mock_sync, mock_title, mock_create_msg, mock_create_conv
    ):
        """无 conversation_id 时应自动创建新对话。"""
        mock_conv = MagicMock()
        mock_conv.id = 42
        mock_create_conv.return_value = mock_conv

        # mock graph ainvoke + aget_state
        self.service.graph = MagicMock()
        self.service.graph.aget_state = AsyncMock(return_value=None)
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="AI reply")]}
        )

        chat_in = ChatRequest(user_input="Hello", conversation_id=None)
        result = await self.service.chat(chat_in, user_id=1)

        mock_create_conv.assert_called_once()
        assert result.conversation_id == 42
        assert result.response == "AI reply"

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    async def test_chat_rejects_foreign_conversation(self, mock_get_conv):
        """传入不属于当前用户的 conversation_id 时应抛出 403。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 999  # 另一个用户
        mock_get_conv.return_value = mock_conv

        self.service.graph.aget_state = AsyncMock(return_value=None)
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="AI reply")]}
        )

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        with pytest.raises(HTTPException) as exc_info:
            await self.service.chat(chat_in, user_id=1)

        assert exc_info.value.status_code == 403

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    async def test_chat_stores_tool_call_messages(self, mock_create_msg, mock_get_conv):
        """当 Graph 返回中间 AIMessage（含 tool_calls）和 ToolMessage 时，均应存入数据库并标记 display=False。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        from langchain_core.messages import ToolMessage

        # 模拟本轮新增消息：中间 AIMessage(含 tool_calls) + ToolMessage + 最终 AIMessage
        intermediate_ai = AIMessage(
            content="",
            tool_calls=[{"id": "call_123", "name": "search_blog", "args": {"query": "vue"}}],
        )
        tool_msg = ToolMessage(content="工具结果", tool_call_id="call_123", name="search_blog")
        final_ai = AIMessage(content="最终回复")

        self.service.graph.aget_state = AsyncMock(
            return_value=MagicMock(values={"messages": []})
        )
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [intermediate_ai, tool_msg, final_ai]}
        )

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        result = await self.service.chat(chat_in, user_id=1)

        assert result.response == "最终回复"

        # 验证共调用了 4 次 create_conversation_message：
        # 第 1 次是用户输入（提前存储），后 3 次是本轮新增消息
        assert mock_create_msg.call_count == 4

        calls = mock_create_msg.call_args_list

        # 第 1 次：用户输入（提前存储）—— 位置参数 (db, conv_id, "user", content)
        args0 = calls[0].args
        assert args0[2] == "user"

        # 第 2 次：中间 AIMessage，含 tool_calls，标记 display=False
        args1 = calls[1].args
        kwargs1 = calls[1].kwargs
        assert args1[2] == "assistant"
        assert kwargs1["metadata"]["display"] is False
        assert kwargs1["metadata"]["tool_calls"][0]["name"] == "search_blog"

        # 第 3 次：ToolMessage，标记 display=False
        args2 = calls[2].args
        kwargs2 = calls[2].kwargs
        assert args2[2] == "tool"
        assert kwargs2["metadata"]["display"] is False
        assert kwargs2["metadata"]["tool_call_id"] == "call_123"

        # 第 4 次：最终 AIMessage，无 metadata（默认展示）
        args3 = calls[3].args
        kwargs3 = calls[3].kwargs
        assert args3[2] == "assistant"
        assert kwargs3["metadata"] is None

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    async def test_chat_marks_tool_call_ai_with_content_as_displayable(
        self, mock_create_msg, mock_get_conv
    ):
        """含 tool_calls 且有正文的 AIMessage 应标记为可展示。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        intermediate_ai = AIMessage(
            content="好的，我帮你联网搜索一下。",
            tool_calls=[
                {"id": "call_123", "name": "web_search", "args": {"query": "python"}}
            ],
        )
        final_ai = AIMessage(content="根据联网搜索结果，我整理如下。")

        self.service.graph.aget_state = AsyncMock(
            return_value=MagicMock(values={"messages": []})
        )
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [intermediate_ai, final_ai]}
        )

        chat_in = ChatRequest(user_input="查一下 Python", conversation_id=1)
        result = await self.service.chat(chat_in, user_id=1)

        assert result.response == "根据联网搜索结果，我整理如下。"
        kwargs1 = mock_create_msg.call_args_list[1].kwargs
        assert kwargs1["metadata"]["display"] is True
        assert kwargs1["metadata"]["tool_calls"][0]["name"] == "web_search"

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    async def test_chat_rejects_nonexistent_conversation(self, mock_get_conv):
        """传入不存在的 conversation_id 时应抛出 404。"""
        mock_get_conv.return_value = None

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        with pytest.raises(HTTPException) as exc_info:
            await self.service.chat(chat_in, user_id=1)

        assert exc_info.value.status_code == 404


class TestGetMessages:
    """测试 get_messages 过滤逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph"):
            self.service = ChatService(self.mock_db)

    @staticmethod
    def _message(
        message_id: int,
        role: str,
        content: str,
        meta: dict | None = None,
    ) -> MagicMock:
        msg = MagicMock()
        msg.id = message_id
        msg.conversation_id = 1
        msg.role = role
        msg.content = content
        msg.meta = meta
        msg.created_at = datetime(2026, 5, 22, tzinfo=timezone.utc)
        return msg

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.list_conversation_messages")
    async def test_filters_hidden_by_default(self, mock_list, mock_get_conv):
        """默认应过滤掉工具结果、系统消息和空内容工具决策消息。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        visible_msg = self._message(1, "assistant", "最终回复")
        hidden_ai = self._message(
            2,
            "assistant",
            "",
            {"display": False, "tool_calls": [{"name": "search_blog"}]},
        )
        tool_msg = self._message(3, "tool", "工具结果", {"display": False})
        system_msg = self._message(4, "system", "系统提示")
        mock_list.return_value = [visible_msg, hidden_ai, tool_msg, system_msg]

        result = await self.service.get_messages(1, 1)
        assert len(result) == 1
        assert result[0].id == visible_msg.id
        assert result[0].content == "最终回复"

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.list_conversation_messages")
    async def test_keeps_tool_call_assistant_content_visible_by_default(
        self, mock_list, mock_get_conv
    ):
        """带 tool_calls 但有正文的 assistant 消息应作为普通可见回复返回。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        pre_tool_reply = self._message(
            1,
            "assistant",
            "好的，我帮你联网搜索一下。",
            {
                "display": True,
                "tool_calls": [{"id": "call_1", "name": "web_search"}],
            },
        )
        tool_msg = self._message(2, "tool", "工具结果", {"display": False})
        final_reply = self._message(3, "assistant", "根据联网搜索结果，我整理如下。")
        mock_list.return_value = [pre_tool_reply, tool_msg, final_reply]

        result = await self.service.get_messages(1, 1)

        assert [msg.content for msg in result] == [
            "好的，我帮你联网搜索一下。",
            "根据联网搜索结果，我整理如下。",
        ]
        assert result[0].meta is None

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.list_conversation_messages")
    async def test_includes_hidden_when_flag_set(self, mock_list, mock_get_conv):
        """include_hidden=True 时应返回完整消息列表。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        visible_msg = self._message(1, "assistant", "最终回复")
        hidden_msg = self._message(
            2,
            "tool",
            "工具结果",
            {"display": False, "tool_call_id": "call_1"},
        )
        mock_list.return_value = [visible_msg, hidden_msg]

        result = await self.service.get_messages(1, 1, include_hidden=True)
        assert len(result) == 2
        assert result[1].meta == {"display": False, "tool_call_id": "call_1"}


class TestGetConversationIfOwned:
    """测试 get_conversation_if_owned 权限校验。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph"):
            self.service = ChatService(self.mock_db)

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_returns_conversation_when_owned(self, mock_get):
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get.return_value = mock_conv

        result = self.service.get_conversation_if_owned(1, 1)
        assert result == mock_conv

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_raises_403_when_not_owner(self, mock_get):
        mock_conv = MagicMock()
        mock_conv.user_id = 999
        mock_get.return_value = mock_conv

        with pytest.raises(HTTPException) as exc_info:
            self.service.get_conversation_if_owned(1, 1)
        assert exc_info.value.status_code == 403

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_raises_404_when_not_found(self, mock_get):
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            self.service.get_conversation_if_owned(1, 1)
        assert exc_info.value.status_code == 404


class TestCountUserMessageChars:
    """测试 _count_user_message_chars 静态方法。"""

    def test_counts_human_message_chars(self):
        """应正确计算 HumanMessage 的内容字符数。"""
        messages = [
            HumanMessage(content="你好"),
            AIMessage(content="Hello"),
            HumanMessage(content="世界"),
        ]
        result = ChatService._count_user_message_chars(messages)
        assert result == 4  # "你好" = 2, "世界" = 2

    def test_skips_non_human_messages(self):
        """非 HumanMessage 不应被计入。"""
        messages = [
            AIMessage(content="AI reply"),
            HumanMessage(content="用户输入"),
        ]
        result = ChatService._count_user_message_chars(messages)
        assert result == 4  # "用户输入" = 4

    def test_empty_list(self):
        """空消息列表应返回 0。"""
        assert ChatService._count_user_message_chars([]) == 0


class TestGenerateCurrentGoal:
    """测试 _generate_current_goal 异步方法。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph"):
            self.service = ChatService(self.mock_db)

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_generates_goal_when_chars_above_threshold(self, mock_get_client):
        """用户消息总字数 >= 200 时，应调用 small model 生成 goal。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(
            return_value=MagicMock(content="  学习 Docker 部署流程  ")
        )
        mock_get_client.return_value = mock_client

        result = await self.service._generate_current_goal(
            conversation_id=1,
            user_input="我想学习 Docker 部署流程，请详细说明",
            previous_goal=None,
            current_messages=[HumanMessage(content="之前的长消息" * 20)],
        )
        assert result == "学习 Docker 部署流程"
        mock_client.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_truncates_long_goal(self, mock_get_client):
        """生成结果超过 200 字时应截断。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(
            return_value=MagicMock(content="x" * 250)
        )
        mock_get_client.return_value = mock_client

        result = await self.service._generate_current_goal(
            conversation_id=1,
            user_input="test",
            previous_goal=None,
            current_messages=[HumanMessage(content="long message" * 20)],
        )
        assert len(result) == 200  # 197 + "..."
        assert result.endswith("...")

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_returns_none_for_short_goal(self, mock_get_client):
        """生成结果短于 5 字时应返回 None。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(
            return_value=MagicMock(content="ok")
        )
        mock_get_client.return_value = mock_client

        result = await self.service._generate_current_goal(
            conversation_id=1,
            user_input="test",
            previous_goal=None,
            current_messages=[HumanMessage(content="long message" * 20)],
        )
        assert result is None

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_falls_back_to_previous_goal_on_error(self, mock_get_client):
        """small model 调用失败时应保留旧 goal。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client

        result = await self.service._generate_current_goal(
            conversation_id=1,
            user_input="test",
            previous_goal="旧目标",
            current_messages=[HumanMessage(content="long message" * 20)],
        )
        assert result == "旧目标"


class TestChatDynamicFields:
    """测试 chat() 方法中动态字段的传入逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph") as mock_get_graph:
            mock_get_graph.return_value = MagicMock()
            self.service = ChatService(self.mock_db)
            self.service.graph = MagicMock()

    @patch("app.services.chat_service.conv_crud.create_ai_conversation")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    @patch.object(ChatService, "_ensure_title_async")
    async def test_new_conversation_passes_dialogue_start_scene(
        self, mock_title, mock_create_msg, mock_create_conv
    ):
        """新对话时应传入 prompt_scene='对话开始'。"""
        mock_conv = MagicMock()
        mock_conv.id = 42
        mock_create_conv.return_value = mock_conv

        self.service.graph.aget_state = AsyncMock(return_value=None)
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="AI reply")]}
        )

        chat_in = ChatRequest(user_input="Hello", conversation_id=None)
        await self.service.chat(chat_in, user_id=1)

        call_kwargs = self.service.graph.ainvoke.call_args[0][0]
        assert call_kwargs["prompt_scene"] == "对话开始"
        assert call_kwargs["conversation_id"] == 42

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    async def test_existing_conversation_passes_continue_scene(
        self, mock_create_msg, mock_get_conv
    ):
        """已有对话时应传入 prompt_scene='持续对话'。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        self.service.graph.aget_state = AsyncMock(
            return_value=MagicMock(values={"messages": []})
        )
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="AI reply")]}
        )

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        await self.service.chat(chat_in, user_id=1)

        call_kwargs = self.service.graph.ainvoke.call_args[0][0]
        assert call_kwargs["prompt_scene"] == "持续对话"

    @patch("app.services.chat_service.conv_crud.create_ai_conversation")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    @patch.object(ChatService, "_ensure_title_async")
    async def test_short_input_no_goal(self, mock_title, mock_create_msg, mock_create_conv):
        """用户输入很短（< 200 字）时不应生成 current_goal。"""
        mock_conv = MagicMock()
        mock_conv.id = 42
        mock_create_conv.return_value = mock_conv

        self.service.graph.aget_state = AsyncMock(return_value=None)
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [AIMessage(content="AI reply")]}
        )

        chat_in = ChatRequest(user_input="短消息", conversation_id=None)
        await self.service.chat(chat_in, user_id=1)

        call_kwargs = self.service.graph.ainvoke.call_args[0][0]
        assert call_kwargs["current_goal"] is None
