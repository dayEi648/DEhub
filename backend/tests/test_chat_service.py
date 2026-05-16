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

    @patch("app.services.chat_service.conv_crud.create_ai_conversation")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    @patch.object(ChatService, "_ensure_title_async")
    @patch.object(ChatService, "_maybe_sync_summary_async")
    def test_chat_creates_new_conversation_when_no_id(
        self, mock_sync, mock_title, mock_create_msg, mock_create_conv
    ):
        """无 conversation_id 时应自动创建新对话。"""
        mock_conv = MagicMock()
        mock_conv.id = 42
        mock_create_conv.return_value = mock_conv

        # mock graph ainvoke
        self.service.graph = MagicMock()
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
        mock_conv.is_deleted = False
        mock_get_conv.return_value = mock_conv

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(self.service.chat(chat_in, user_id=1))

        assert exc_info.value.status_code == 403

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_chat_rejects_deleted_conversation(self, mock_get_conv):
        """传入已删除的 conversation_id 时应抛出 404。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_conv.is_deleted = True
        mock_get_conv.return_value = mock_conv

        chat_in = ChatRequest(user_input="Hello", conversation_id=1)
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(self.service.chat(chat_in, user_id=1))

        assert exc_info.value.status_code == 404


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
        mock_conv.is_deleted = False
        mock_get.return_value = mock_conv

        result = self.service.get_conversation_if_owned(1, 1)
        assert result == mock_conv

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_raises_404_when_deleted(self, mock_get):
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_conv.is_deleted = True
        mock_get.return_value = mock_conv

        with pytest.raises(HTTPException) as exc_info:
            self.service.get_conversation_if_owned(1, 1)
        assert exc_info.value.status_code == 404

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    def test_raises_403_when_not_owner(self, mock_get):
        mock_conv = MagicMock()
        mock_conv.user_id = 999
        mock_conv.is_deleted = False
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
