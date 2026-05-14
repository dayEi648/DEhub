import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure import llm_client as llm_module
from app.infrastructure.llm_client import (
    get_llm_client,
    init_llm_client,
    close_llm_client,
)


class TestLifecycle:
    @pytest.fixture(autouse=True)
    def reset_global(self):
        llm_module._llm_client = None
        yield
        llm_module._llm_client = None

    def test_get_llm_client_before_init_raises(self):
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

        with patch("app.infrastructure.llm_client.ChatOpenAI") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance

            await init_llm_client()
            client = get_llm_client()

            assert client is mock_instance
            mock_cls.assert_called_once_with(
                api_key="k",
                base_url="https://x.com",
                model="m",
                max_tokens=10,
                temperature=0.0,
                timeout=5,
            )

    @pytest.mark.asyncio
    async def test_close_sets_none(self, monkeypatch):
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_BASE_URL", "https://x.com")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_API_KEY", "k")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MODEL", "m")
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_MAX_TOKENS", 10)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TEMPERATURE", 0.0)
        monkeypatch.setattr(llm_module.settings, "LLM_MAIN_TIMEOUT", 5)

        with patch("app.infrastructure.llm_client.ChatOpenAI"):
            await init_llm_client()
            await close_llm_client()
            with pytest.raises(ValueError, match="未初始化"):
                get_llm_client()
