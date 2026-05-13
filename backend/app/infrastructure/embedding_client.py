import asyncio
from typing import AsyncGenerator

import httpx

from app.core.config import settings

_embedding_client: "EmbeddingClient | None" = None

# 阿里云百炼 text-embedding-v4 单次请求最多 25 条文本
_MAX_BATCH_SIZE = 25


class EmbeddingClient:
    """
    异步 Embedding HTTP 客户端，封装 OpenAI 兼容接口的向量嵌入调用。

    适配阿里云百炼平台 text-embedding-v4 等模型。
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.EMBEDDING_BASE_URL,
            headers={"Authorization": f"Bearer {settings.EMBEDDING_API_KEY}"},
            timeout=settings.EMBEDDING_TIMEOUT,
        )

    async def aembed(self, texts: list[str]) -> list[list[float]]:
        """
        批量获取文本嵌入向量。

        自动按服务商批量上限切分请求，最后按原始输入顺序合并结果。

        :param texts: 待嵌入的文本列表
        :return: 与 texts 一一对应的嵌入向量列表
        :raises httpx.HTTPStatusError: HTTP 状态码异常
        """
        if not texts:
            return []

        results: list[list[float]] = []
        for i in range(0, len(texts), _MAX_BATCH_SIZE):
            batch = texts[i : i + _MAX_BATCH_SIZE]
            batch_results = await self._embed_batch(batch)
            results.extend(batch_results)

        return results

    async def aembed_single(self, text: str) -> list[float]:
        """
        获取单条文本的嵌入向量。

        :param text: 待嵌入的文本
        :return: 嵌入向量
        """
        results = await self.aembed([text])
        return results[0] if results else []

    async def astream_embed(
        self, texts: list[str]
    ) -> AsyncGenerator[list[float], None]:
        """
        批量获取嵌入向量，逐批 yield 结果。

        适合内存敏感或需要渐进式处理的场景。
        """
        if not texts:
            return

        for i in range(0, len(texts), _MAX_BATCH_SIZE):
            batch = texts[i : i + _MAX_BATCH_SIZE]
            batch_results = await self._embed_batch(batch)
            for vec in batch_results:
                yield vec

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """发送单批嵌入请求。"""
        payload: dict = {
            "model": settings.EMBEDDING_MODEL,
            "input": texts,
            "encoding_format": "float",
        }
        if settings.EMBEDDING_DIMENSION is not None:
            payload["dimensions"] = settings.EMBEDDING_DIMENSION

        resp = await self._client.post("/v1/embeddings", json=payload)
        resp.raise_for_status()
        return _extract_embeddings(resp.json())

    async def close(self) -> None:
        """关闭底层 HTTP 连接池。"""
        await self._client.aclose()


def _extract_embeddings(data: dict) -> list[list[float]]:
    """
    从响应 JSON 中提取嵌入向量列表，按 index 排序以确保与输入顺序一致。
    """
    items = data.get("data") or []
    if not items:
        return []

    sorted_items = sorted(items, key=lambda x: x.get("index", 0))
    return [item.get("embedding", []) for item in sorted_items]


# ---------------------------------------------------------------------------
# 生命周期管理（由 FastAPI lifespan 调用）
# ---------------------------------------------------------------------------

async def init_embedding_client() -> None:
    """初始化全局 EmbeddingClient 单例。"""
    global _embedding_client
    _embedding_client = EmbeddingClient()


async def close_embedding_client() -> None:
    """关闭全局 EmbeddingClient 单例并释放引用。"""
    global _embedding_client
    if _embedding_client:
        await _embedding_client.close()
        _embedding_client = None


def get_embedding_client() -> EmbeddingClient:
    """
    获取已初始化的 EmbeddingClient 实例。

    :raises ValueError: 若尚未调用 init_embedding_client()
    """
    if _embedding_client is None:
        raise ValueError(
            "EmbeddingClient 未初始化，请先调用 init_embedding_client()"
        )
    return _embedding_client
