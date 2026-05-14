import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.core.security import get_current_user


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.permission = 0
    return user


def _async_iter(items):
    async def _gen():
        for item in items:
            yield item
    return _gen()


@pytest.fixture(autouse=True)
def mock_llm_clients():
    """全局 mock LLM 和 Redis 客户端，避免 lifespan 未初始化导致的错误。"""
    main = MagicMock()
    main.astream = MagicMock(return_value=_async_iter(["Hel", "lo"]))
    main.ainvoke = AsyncMock(return_value="Title")
    small = MagicMock()
    small.ainvoke = AsyncMock(return_value="Title")
    with patch(
        "app.services.chat_graph_service.get_llm_client", return_value=main
    ), patch(
        "app.services.chat_graph_service.get_llm_small_client", return_value=small
    ), patch(
        "app.infrastructure.redis_checkpoint.get_redis_client", return_value=MagicMock()
    ):
        yield


# ---------- SSE 流式对话 ----------

class TestStreamChat:
    def test_new_conversation_sse(self, client, mock_user):
        """新对话流式接口返回 SSE 格式。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            async def _mock_stream(*args, **kwargs):
                for chunk in ["Hel", "lo"]:
                    yield chunk

            with patch(
                "app.services.chat_graph_service.ChatGraphService.stream_chat",
                _mock_stream,
            ):
                response = client.post(
                    "/api/v1/chat/stream",
                    json={"content": "hi"},
                )

            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            body = response.text
            assert "data: Hel" in body
            assert "data: lo" in body
            assert "data: [DONE]" in body
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_existing_conversation_sse(self, client, mock_user):
        """已有对话流式接口。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            mock_conv = MagicMock()
            mock_conv.id = 5

            async def _mock_stream(*args, **kwargs):
                for chunk in ["Hel", "lo"]:
                    yield chunk

            with patch(
                "app.services.chat_graph_service.ChatGraphService.get_conversation_or_raise",
                return_value=mock_conv,
            ), patch(
                "app.services.chat_graph_service.ChatGraphService.stream_chat",
                _mock_stream,
            ):
                response = client.post(
                    "/api/v1/chat/stream",
                    json={"conversation_id": 5, "content": "next"},
                )

            assert response.status_code == 200
            assert "data: Hel" in response.text
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_stream_chat_validation_error(self, client, mock_user):
        """content 为空时返回 422。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            response = client.post(
                "/api/v1/chat/stream",
                json={"content": ""},
            )
            assert response.status_code == 422
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_stream_chat_unauthorized(self, client):
        """未认证返回 401 或 403。"""
        response = client.post("/api/v1/chat/stream", json={"content": "hi"})
        assert response.status_code in (401, 403)


# ---------- 对话管理 ----------

class TestConversationManagement:
    def test_list_conversations(self, client, mock_user):
        """获取对话列表。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch(
                "app.services.chat_graph_service.ChatGraphService.list_conversations",
                new_callable=AsyncMock,
                return_value=([], 0),
            ):
                response = client.get("/api/v1/chat/conversations")

            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_list_messages(self, client, mock_user):
        """获取消息列表。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch(
                "app.services.chat_graph_service.ChatGraphService.get_messages",
                new_callable=AsyncMock,
                return_value=[],
            ):
                response = client.get("/api/v1/chat/conversations/3/messages")

            assert response.status_code == 200
            assert response.json() == []
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_delete_conversation(self, client, mock_user):
        """删除对话。"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        try:
            with patch(
                "app.services.chat_graph_service.ChatGraphService.delete_conversation",
                new_callable=AsyncMock,
                return_value=None,
            ) as mock_delete:
                response = client.delete("/api/v1/chat/conversations/5")

            assert response.status_code == 204
            mock_delete.assert_awaited_once_with(5, 1)
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_delete_conversation_unauthorized(self, client):
        """未认证删除对话。"""
        response = client.delete("/api/v1/chat/conversations/5")
        assert response.status_code in (401, 403)
