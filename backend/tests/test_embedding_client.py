import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.infrastructure import embedding_client as emb_module
from app.infrastructure.embedding_client import (
    EmbeddingClient,
    _extract_embeddings,
    get_embedding_client,
    init_embedding_client,
    close_embedding_client,
)


# ---------- _extract_embeddings ----------

class TestExtractEmbeddings:
    def test_normal(self):
        data = {
            "data": [
                {"index": 1, "embedding": [0.1, 0.2]},
                {"index": 0, "embedding": [0.3, 0.4]},
            ]
        }
        result = _extract_embeddings(data)
        # 按 index 排序
        assert result == [[0.3, 0.4], [0.1, 0.2]]

    def test_empty_data(self):
        assert _extract_embeddings({"data": []}) == []
        assert _extract_embeddings({}) == []

    def test_missing_embedding(self):
        data = {"data": [{"index": 0}]}
        assert _extract_embeddings(data) == [[]]


# ---------- EmbeddingClient 集成测试 ----------

class TestEmbeddingClient:
    @pytest.fixture(autouse=True)
    def patch_settings(self, monkeypatch):
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_BASE_URL", "https://api.example.com")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_API_KEY", "test-key")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_MODEL", "text-embedding-v4")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_DIMENSION", 1024)
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_TIMEOUT", 30)

    @pytest.fixture
    def mock_httpx_client(self):
        with patch("app.infrastructure.embedding_client.httpx.AsyncClient") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_aembed_empty_list(self, mock_httpx_client):
        client = EmbeddingClient()
        result = await client.aembed([])
        assert result == []
        mock_httpx_client.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_aembed_single_batch(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2]},
                {"index": 1, "embedding": [0.3, 0.4]},
            ]
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = EmbeddingClient()
        result = await client.aembed(["hello", "world"])

        assert result == [[0.1, 0.2], [0.3, 0.4]]
        mock_httpx_client.post.assert_awaited_once()
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "/v1/embeddings"
        payload = call_args[1]["json"]
        assert payload["model"] == "text-embedding-v4"
        assert payload["input"] == ["hello", "world"]
        assert payload["encoding_format"] == "float"
        assert payload["dimensions"] == 1024

    @pytest.mark.asyncio
    async def test_aembed_multi_batch(self, mock_httpx_client):
        """超过 25 条时自动分批。"""
        def _side_effect(*args, **kwargs):
            batch_size = len(kwargs["json"]["input"])
            resp = MagicMock()
            resp.json.return_value = {
                "data": [{"index": i, "embedding": [0.9]} for i in range(batch_size)]
            }
            return resp

        mock_httpx_client.post = AsyncMock(side_effect=_side_effect)

        client = EmbeddingClient()
        texts = ["x"] * 27
        result = await client.aembed(texts)

        assert len(result) == 27
        assert mock_httpx_client.post.await_count == 2
        # 第一批 25 条，第二批 2 条
        calls = mock_httpx_client.post.call_args_list
        assert len(calls[0][1]["json"]["input"]) == 25
        assert len(calls[1][1]["json"]["input"]) == 2

    @pytest.mark.asyncio
    async def test_aembed_single(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"index": 0, "embedding": [0.5, 0.6]}]
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = EmbeddingClient()
        result = await client.aembed_single("hello")

        assert result == [0.5, 0.6]
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"]["input"] == ["hello"]

    @pytest.mark.asyncio
    async def test_astream_embed(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"index": 0, "embedding": [0.1]},
                {"index": 1, "embedding": [0.2]},
            ]
        }
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = EmbeddingClient()
        chunks = [c async for c in client.astream_embed(["a", "b"])]

        assert chunks == [[0.1], [0.2]]

    @pytest.mark.asyncio
    async def test_aembed_raises_on_http_error(self, mock_httpx_client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = EmbeddingClient()
        with pytest.raises(Exception, match="429 Too Many Requests"):
            await client.aembed(["hello"])

    @pytest.mark.asyncio
    async def test_dimension_none_omitted(self, monkeypatch, mock_httpx_client):
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_DIMENSION", None)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": [{"index": 0, "embedding": [0.1]}]}
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = EmbeddingClient()
        await client.aembed(["hello"])

        payload = mock_httpx_client.post.call_args[1]["json"]
        assert "dimensions" not in payload

    @pytest.mark.asyncio
    async def test_close(self, mock_httpx_client):
        mock_httpx_client.aclose = AsyncMock()
        client = EmbeddingClient()
        await client.close()
        mock_httpx_client.aclose.assert_awaited_once()


# ---------- 生命周期管理 ----------

class TestLifecycle:
    @pytest.fixture(autouse=True)
    def reset_global(self):
        emb_module._embedding_client = None
        yield
        emb_module._embedding_client = None

    @pytest.mark.asyncio
    async def test_get_before_init_raises(self):
        with pytest.raises(ValueError, match="未初始化"):
            get_embedding_client()

    @pytest.mark.asyncio
    async def test_init_and_get(self, monkeypatch):
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_BASE_URL", "https://x.com")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_API_KEY", "k")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_MODEL", "m")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_DIMENSION", None)
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_TIMEOUT", 5)

        await init_embedding_client()
        client = get_embedding_client()
        assert isinstance(client, EmbeddingClient)

    @pytest.mark.asyncio
    async def test_close_sets_none(self, monkeypatch):
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_BASE_URL", "https://x.com")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_API_KEY", "k")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_MODEL", "m")
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_DIMENSION", None)
        monkeypatch.setattr(emb_module.settings, "EMBEDDING_TIMEOUT", 5)

        await init_embedding_client()
        await close_embedding_client()
        with pytest.raises(ValueError, match="未初始化"):
            get_embedding_client()
