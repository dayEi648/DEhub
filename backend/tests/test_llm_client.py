import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.infrastructure import llm_client as llm_module
from app.infrastructure.llm_client import (
    LLMClient,
    _inject_system,
    _extract_content,
    _parse_sse,
    get_llm_client,
    init_llm_client,
    close_llm_client,
)


# ---------- 辅助函数：将列表包装为异步生成器 ----------
def _async_iter(items):
    async def _gen():
        for item in items:
            yield item
    return _gen()


# ---------- _inject_system ----------

class TestInjectSystem:
    def test_no_system_prompt(self):
        messages = [{"role": "user", "content": "hi"}]
        result = _inject_system(messages, None)
        assert result == messages

    def test_already_has_system(self):
        messages = [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        result = _inject_system(messages, "new_sys")
        assert result == messages

    def test_injects_system(self):
        messages = [{"role": "user", "content": "hi"}]
        result = _inject_system(messages, "be kind")
        assert result == [{"role": "system", "content": "be kind"}, {"role": "user", "content": "hi"}]


# ---------- _extract_content ----------

class TestExtractContent:
    def test_normal(self):
        data = {"choices": [{"message": {"content": "hello"}}]}
        assert _extract_content(data) == "hello"

    def test_empty_choices(self):
        assert _extract_content({"choices": []}) == ""

    def test_no_choices_key(self):
        assert _extract_content({}) == ""

    def test_no_message(self):
        assert _extract_content({"choices": [{}]}) == ""

    def test_no_content(self):
        assert _extract_content({"choices": [{"message": {}}]}) == ""


# ---------- _parse_sse ----------

class TestParseSSE:
    @pytest.mark.asyncio
    async def test_yields_content(self):
        lines = [
            "data: {\"choices\":[{\"delta\":{\"content\":\"Hel\"}}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"lo\"}}]}",
            "data: [DONE]",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["Hel", "lo"]

    @pytest.mark.asyncio
    async def test_skips_empty_lines(self):
        lines = ["", "data: {\"choices\":[{\"delta\":{\"content\":\"A\"}}]}", ""]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["A"]

    @pytest.mark.asyncio
    async def test_skips_non_data_lines(self):
        lines = [": heartbeat", "data: {\"choices\":[{\"delta\":{\"content\":\"B\"}}]}"]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["B"]

    @pytest.mark.asyncio
    async def test_skips_invalid_json(self):
        lines = [
            "data: not-json",
            "data: {\"choices\":[{\"delta\":{\"content\":\"C\"}}]}",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["C"]

    @pytest.mark.asyncio
    async def test_skips_none_delta(self):
        lines = [
            "data: {\"choices\":[{\"delta\":null}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"D\"}}]}",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["D"]

    @pytest.mark.asyncio
    async def test_skips_empty_choices(self):
        lines = [
            "data: {\"choices\":[]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"E\"}}]}",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["E"]

    @pytest.mark.asyncio
    async def test_skips_empty_delta_content(self):
        lines = [
            "data: {\"choices\":[{\"delta\":{\"content\":\"\"}}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"F\"}}]}",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)

        chunks = [c async for c in _parse_sse(mock_resp)]
        assert chunks == ["F"]


# ---------- LLMClient 集成测试 ----------

class TestLLMClient:
    @pytest.fixture(autouse=True)
    def patch_settings(self, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_BASE_URL", "https://api.example.com")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_API_KEY", "test-key")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MODEL", "gpt-test")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MAX_TOKENS", 100)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TEMPERATURE", 0.5)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TIMEOUT", 30)

    @pytest.fixture
    def mock_httpx_client(self):
        with patch("app.infrastructure.llm_client.httpx.AsyncClient") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            yield mock_instance

    # --- achat ---

    @pytest.mark.asyncio
    async def test_achat_success(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "Hello!"}}]}
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        result = await client.achat([{"role": "user", "content": "hi"}])

        assert result == "Hello!"
        mock_httpx_client.post.assert_awaited_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "/v1/chat/completions"
        assert call_args[1]["json"]["stream"] is False
        assert call_args[1]["json"]["messages"] == [{"role": "user", "content": "hi"}]

    @pytest.mark.asyncio
    async def test_achat_raises_on_http_error(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        with pytest.raises(Exception, match="401 Unauthorized"):
            await client.achat([{"role": "user", "content": "hi"}])

    @pytest.mark.asyncio
    async def test_achat_empty_choices(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": []}
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        result = await client.achat([{"role": "user", "content": "hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_achat_injects_system_prompt(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        await client.achat([{"role": "user", "content": "hi"}], system_prompt="sys")

        payload = mock_httpx_client.post.call_args[1]["json"]
        assert payload["messages"][0] == {"role": "system", "content": "sys"}

    # --- astream_chat ---

    @pytest.mark.asyncio
    async def test_astream_chat_success(self, mock_httpx_client):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hi"}}]}',
            "data: [DONE]",
        ]
        mock_resp = MagicMock()
        mock_resp.aiter_lines = lambda: _async_iter(lines)
        mock_resp.raise_for_status = MagicMock()

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_client.stream = MagicMock(return_value=mock_ctx)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        chunks = [c async for c in client.astream_chat([{"role": "user", "content": "hi"}])]

        assert chunks == ["Hi"]
        mock_httpx_client.stream.assert_called_once()
        call_kwargs = mock_httpx_client.stream.call_args[1]
        assert call_kwargs["json"]["stream"] is True

    @pytest.mark.asyncio
    async def test_astream_chat_raises_on_http_error(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("503 Service Unavailable")

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_client.stream = MagicMock(return_value=mock_ctx)

        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        with pytest.raises(Exception, match="503 Service Unavailable"):
            async for _ in client.astream_chat([{"role": "user", "content": "hi"}]):
                pass

    # --- close ---

    @pytest.mark.asyncio
    async def test_close(self, mock_httpx_client):
        mock_httpx_client.aclose = AsyncMock()
        client = LLMClient(
            base_url="https://api.example.com",
            api_key="test-key",
            model="gpt-test",
            max_tokens=100,
            temperature=0.5,
            timeout=30,
        )
        await client.close()
        mock_httpx_client.aclose.assert_awaited_once()


# ---------- 生命周期管理 ----------

class TestLifecycle:
    @pytest.fixture(autouse=True)
    def reset_global(self):
        llm_module._llm_client = None
        yield
        llm_module._llm_client = None

    @pytest.mark.asyncio
    async def test_get_llm_client_before_init_raises(self):
        with pytest.raises(ValueError, match="未初始化"):
            get_llm_client()

    @pytest.mark.asyncio
    async def test_init_and_get(self, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_BASE_URL", "https://x.com")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_API_KEY", "k")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MODEL", "m")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MAX_TOKENS", 10)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TEMPERATURE", 0.0)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TIMEOUT", 5)

        await init_llm_client()
        client = get_llm_client()
        assert isinstance(client, LLMClient)

    @pytest.mark.asyncio
    async def test_close_sets_none(self, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_BASE_URL", "https://x.com")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_API_KEY", "k")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MODEL", "m")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MAX_TOKENS", 10)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TEMPERATURE", 0.0)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TIMEOUT", 5)

        await init_llm_client()
        await close_llm_client()
        with pytest.raises(ValueError, match="未初始化"):
            get_llm_client()
