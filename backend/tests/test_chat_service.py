"""chat_service 单元测试。"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from langchain_core.messages import AIMessage

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
    def test_chat_creates_new_conversation_when_no_id(
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
        result = asyncio.run(self.service.chat(chat_in, user_id=1))

        mock_create_conv.assert_called_once()
        assert result.conversation_id == 42
        assert result.response == "AI reply"

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_chat_rejects_foreign_conversation(self, mock_get_conv):
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
            asyncio.run(self.service.chat(chat_in, user_id=1))

        assert exc_info.value.status_code == 403

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    def test_chat_stores_tool_call_messages(self, mock_create_msg, mock_get_conv):
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
        result = asyncio.run(self.service.chat(chat_in, user_id=1))

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
    def test_chat_rejects_nonexistent_conversation(self, mock_get_conv):
        """传入不存在的 conversation_id 时应抛出 404。"""
        mock_get_conv.return_value = None

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(self.service.chat(chat_in, user_id=1))

        assert exc_info.value.status_code == 404


class TestGetMessages:
    """测试 get_messages 过滤逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph"):
            self.service = ChatService(self.mock_db)

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.list_conversation_messages")
    def test_filters_hidden_by_default(self, mock_list, mock_get_conv):
        """默认应过滤掉 meta.display=False 的消息。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        visible_msg = MagicMock()
        visible_msg.meta = None
        hidden_msg = MagicMock()
        hidden_msg.meta = {"display": False}
        mock_list.return_value = [visible_msg, hidden_msg]

        result = asyncio.run(self.service.get_messages(1, 1))
        assert len(result) == 1
        assert result[0] == visible_msg

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.list_conversation_messages")
    def test_includes_hidden_when_flag_set(self, mock_list, mock_get_conv):
        """include_hidden=True 时应返回完整消息列表。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        visible_msg = MagicMock()
        visible_msg.meta = None
        hidden_msg = MagicMock()
        hidden_msg.meta = {"display": False}
        mock_list.return_value = [visible_msg, hidden_msg]

        result = asyncio.run(self.service.get_messages(1, 1, include_hidden=True))
        assert len(result) == 2


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
