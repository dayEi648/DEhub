"""chat_service 单元测试。"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

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
        assert kwargs1["metadata"]["display"] is False
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
    async def test_hides_tool_call_assistant_content_by_default(
        self, mock_list, mock_get_conv
    ):
        """带 tool_calls 的 assistant 消息默认应对普通用户隐藏。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        pre_tool_reply = self._message(
            1,
            "assistant",
            "好的，我帮你联网搜索一下。",
            {
                "display": False,
                "tool_calls": [{"id": "call_1", "name": "web_search"}],
            },
        )
        tool_msg = self._message(2, "tool", "工具结果", {"display": False})
        final_reply = self._message(3, "assistant", "根据联网搜索结果，我整理如下。")
        mock_list.return_value = [pre_tool_reply, tool_msg, final_reply]

        result = await self.service.get_messages(1, 1)

        assert [msg.content for msg in result] == [
            "根据联网搜索结果，我整理如下。",
        ]

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


class TestChatCompact:
    """测试 AIchat compact 相关辅助逻辑。"""

    def setup_method(self):
        self.mock_db = MagicMock()
        with patch("app.services.chat_service.get_chat_graph"):
            self.service = ChatService(self.mock_db)

    def test_build_compact_payload_filters_internal_messages_and_keeps_latest_turn(self):
        """compact 输入应排除 SystemMessage、tool_calls AIMessage 和最新一轮对话。"""
        tool_ai = AIMessage(
            content="我要调用工具",
            tool_calls=[{"id": "call_1", "name": "web_search", "args": {}}],
        )
        messages = [
            SystemMessage(content="system"),
            HumanMessage(content="旧问题"),
            tool_ai,
            ToolMessage(content="工具结果", tool_call_id="call_1", name="web_search"),
            AIMessage(content="旧回答"),
            HumanMessage(content="最新问题"),
            AIMessage(
                content="最新轮工具调用",
                tool_calls=[{"id": "call_2", "name": "web_search", "args": {}}],
            ),
            ToolMessage(content="最新轮工具结果", tool_call_id="call_2", name="web_search"),
            AIMessage(content="最新回答"),
        ]

        transcript, retained = self.service._build_compact_payload(messages)

        assert "system" not in transcript
        assert "我要调用工具" not in transcript
        assert "最新问题" not in transcript
        assert "最新回答" not in transcript
        assert "旧问题" in transcript
        assert "旧回答" in transcript
        assert [m.content for m in retained] == ["最新问题", "最新回答"]

    @pytest.mark.asyncio
    async def test_apply_compact_summary_replaces_checkpoint_messages(self):
        """写入 compact summary 时应整体替换 checkpoint 消息，避免旧历史残留。"""
        config = {"configurable": {"thread_id": 1}}
        self.service.graph = MagicMock()
        self.service.graph.aupdate_state = AsyncMock()
        retained = [HumanMessage(content="最新问题"), AIMessage(content="最新回答")]

        await self.service._apply_compact_summary(
            config=config,
            summary="摘要内容",
            retained_messages=retained,
            current_goal="当前目标",
        )

        update = self.service.graph.aupdate_state.call_args.args[1]
        assert update["messages"][0].id == REMOVE_ALL_MESSAGES
        assert update["messages"][1].content == "摘要内容"
        assert update["messages"][1].additional_kwargs["compact_summary"] is True
        assert [m.content for m in update["messages"][2:]] == ["最新问题", "最新回答"]
        assert update["current_goal"] == "当前目标"
        assert "context_summary" not in update
        assert "compacted" not in update

    def test_compact_summary_message_is_sanitized_for_api_response(self):
        """消息列表 API 不应暴露真实 compact summary，只返回占位提示。"""
        message = MagicMock()
        message.id = 7
        message.conversation_id = 1
        message.role = "assistant"
        message.content = "真实摘要内容"
        message.meta = {"compact_summary": True, "display": True}
        message.created_at = datetime(2026, 5, 22, tzinfo=timezone.utc)

        result = self.service._to_message_response(message, include_hidden=False)

        assert result.content == "已自动压缩上下文"
        assert result.meta == {"compact_summary": True}

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_client")
    async def test_should_compact_uses_fixed_85_percent_threshold(self, mock_get_client):
        """上下文 token 达到 1M 的 85% 时才触发 compact。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_client.get_num_tokens_from_messages.return_value = 849_999
        below = await self.service._should_compact(
            {"messages": [HumanMessage(content="hello"), AIMessage(content="reply")]}
        )

        mock_client.get_num_tokens_from_messages.return_value = 850_000
        reached = await self.service._should_compact(
            {"messages": [HumanMessage(content="hello"), AIMessage(content="reply")]}
        )

        assert below is False
        assert reached is True

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_sync_redis_client")
    async def test_conversation_lock_returns_409_when_lock_exists(self, mock_get_redis):
        """同一对话已有请求执行时应拒绝新请求。"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = False
        mock_get_redis.return_value = mock_redis

        with pytest.raises(HTTPException) as exc_info:
            await self.service._acquire_conversation_lock(1)

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_generate_compact_summary_retries_empty_response(self, mock_get_client):
        """small model 返回空摘要时应重试一次。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(
            side_effect=[
                MagicMock(content="   "),
                MagicMock(content="有效摘要"),
            ]
        )
        mock_get_client.return_value = mock_client

        result = await self.service._generate_compact_summary("user: 历史消息")

        assert result == "有效摘要"
        assert mock_client.ainvoke.await_count == 2

    @pytest.mark.asyncio
    async def test_maybe_compact_returns_false_when_persist_fails(self):
        """compact 入库失败不应向外抛出，主回复流程应能继续返回。"""
        self.service._should_compact = AsyncMock(return_value=True)
        self.service._generate_compact_summary = AsyncMock(return_value="摘要")
        self.service._persist_compact_summary = AsyncMock(
            side_effect=Exception("db error")
        )
        self.service._apply_compact_summary = AsyncMock()

        result = await self.service._maybe_compact_after_response(
            config={"configurable": {"thread_id": 1}},
            conversation_id=1,
            result={"messages": [
                HumanMessage(content="旧问题"),
                AIMessage(content="旧回答"),
                HumanMessage(content="最新问题"),
                AIMessage(content="最新回答"),
            ]},
            current_goal="当前目标",
        )

        assert result is False
        self.service._apply_compact_summary.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.services.chat_service.get_llm_small_client")
    async def test_maybe_compact_retries_and_returns_false_on_small_model_failure(
        self, mock_get_client
    ):
        """compact 失败应重试一次，仍失败则返回 False，不阻断主回复。"""
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=Exception("small model error"))
        mock_get_client.return_value = mock_client

        self.service._should_compact = AsyncMock(return_value=True)
        self.service._persist_compact_summary = AsyncMock()
        self.service._apply_compact_summary = AsyncMock()

        result = await self.service._maybe_compact_after_response(
            config={"configurable": {"thread_id": 1}},
            conversation_id=1,
            result={"messages": [
                HumanMessage(content="旧问题"),
                AIMessage(content="旧回答"),
                HumanMessage(content="最新问题"),
                AIMessage(content="最新回答"),
            ]},
            current_goal=None,
        )

        assert result is False
        assert mock_client.ainvoke.await_count == 2
        self.service._persist_compact_summary.assert_not_called()
        self.service._apply_compact_summary.assert_not_called()


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
            current_messages=[
                AIMessage(
                    content="历史摘要",
                    additional_kwargs={"compact_summary": True},
                ),
                HumanMessage(content="之前的长消息" * 20),
            ],
        )
        assert result == "学习 Docker 部署流程"
        mock_client.ainvoke.assert_called_once()
        prompt = mock_client.ainvoke.call_args.args[0][0].content
        assert "历史摘要" in prompt

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
        assert "context_summary" not in call_kwargs
        assert "compacted" not in call_kwargs

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
        """新对话短输入无历史 goal 时不应生成 current_goal。"""
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

    @patch("app.services.chat_service.conv_crud.get_ai_conversation_by_id")
    @patch("app.services.chat_service.msg_crud.create_conversation_message")
    async def test_short_input_preserves_existing_goal(self, mock_create_msg, mock_get_conv):
        """短输入不重新生成 goal 时，应保留 checkpoint 中已有 current_goal。"""
        mock_conv = MagicMock()
        mock_conv.user_id = 1
        mock_get_conv.return_value = mock_conv

        self.service.graph.aget_state = AsyncMock(
            return_value=MagicMock(values={
                "messages": [HumanMessage(content="短历史")],
                "current_goal": "旧目标",
            })
        )
        self.service.graph.ainvoke = AsyncMock(
            return_value={"messages": [
                HumanMessage(content="短历史"),
                HumanMessage(content="继续"),
                AIMessage(content="AI reply"),
            ]}
        )
        self.service._maybe_compact_after_response = AsyncMock(return_value=False)

        chat_in = ChatRequest(user_input="继续", conversation_id=1)
        await self.service.chat(chat_in, user_id=1)

        call_kwargs = self.service.graph.ainvoke.call_args[0][0]
        assert call_kwargs["current_goal"] == "旧目标"
