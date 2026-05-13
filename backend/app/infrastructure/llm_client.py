import json
import asyncio
from typing import AsyncGenerator

import httpx

from app.core.config import settings

_llm_client: "LLMClient | None" = None
_llm_small_client: "LLMClient | None" = None


class LLMClient:
    """
    异步 LLM HTTP 客户端，封装 OpenAI 兼容接口的流式与非流式调用。
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        max_tokens: int,
        temperature: float,
        timeout: int,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    async def achat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        """
        非流式对话。

        :param messages: 形如 [{"role": "user", "content": "..."}, ...]
        :param system_prompt: 若传入且 messages 中无 system 角色，则自动注入到头部
        :return: LLM 返回的完整文本内容
        :raises httpx.HTTPStatusError: HTTP 状态码异常
        """
        payload = self._build_payload(messages, system_prompt, stream=False)
        resp = await self._client.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        return _extract_content(resp.json())

    async def astream_chat(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式对话，逐字 yield 文本内容。

        :param messages: 同 achat
        :param system_prompt: 同 achat
        :yield: 每次增量文本片段
        :raises httpx.HTTPStatusError: HTTP 状态码异常
        """
        payload = self._build_payload(messages, system_prompt, stream=True)
        async with self._client.stream(
            "POST", "/v1/chat/completions", json=payload
        ) as response:
            response.raise_for_status()
            async for text in _parse_sse(response):
                yield text

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None,
        stream: bool,
    ) -> dict:
        """构造请求体。"""
        return {
            "model": self._model,
            "messages": _inject_system(messages, system_prompt),
            "stream": stream,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
        }

    async def close(self) -> None:
        """关闭底层 HTTP 连接池。"""
        await self._client.aclose()


def _inject_system(
    messages: list[dict[str, str]],
    system_prompt: str | None,
) -> list[dict[str, str]]:
    """
    若提供了 system_prompt 且 messages 中不存在 system 角色，
    则在消息列表头部注入 system 消息。
    """
    if system_prompt and not any(m.get("role") == "system" for m in messages):
        return [{"role": "system", "content": system_prompt}, *messages]
    return messages


async def _parse_sse(response: httpx.Response) -> AsyncGenerator[str, None]:
    """
    解析 SSE 流响应，逐段 yield delta.content。

    跳过空行、非 data: 行、[DONE] 终止标记、以及无法解析的 JSON。
    """
    async for line in response.aiter_lines():
        if not line:
            continue
        if not line.startswith("data: "):
            continue

        data = line[6:]
        if data == "[DONE]":
            break

        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            continue

        choices = chunk.get("choices") or []
        if not choices:
            continue

        delta = (choices[0].get("delta") or {}).get("content", "")
        if delta:
            yield delta


def _extract_content(data: dict) -> str:
    """从非流式响应 JSON 中提取文本内容。"""
    choices = data.get("choices") or []
    if not choices:
        return ""
    return (choices[0].get("message") or {}).get("content", "")


# ---------------------------------------------------------------------------
# 生命周期管理（由 FastAPI lifespan 调用）
# ---------------------------------------------------------------------------

async def init_llm_client() -> None:
    """初始化全局 LLMClient 单例（main model）。"""
    global _llm_client
    _llm_client = LLMClient(
        base_url=settings.LLM_MAIN_BASE_URL,
        api_key=settings.LLM_MAIN_API_KEY,
        model=settings.LLM_MAIN_MODEL,
        max_tokens=settings.LLM_MAIN_MAX_TOKENS,
        temperature=settings.LLM_MAIN_TEMPERATURE,
        timeout=settings.LLM_MAIN_TIMEOUT,
    )


async def init_llm_small_client() -> None:
    """初始化全局 LLMClient 单例（small model）。"""
    global _llm_small_client
    _llm_small_client = LLMClient(
        base_url=settings.LLM_SMALL_BASE_URL,
        api_key=settings.LLM_SMALL_API_KEY,
        model=settings.LLM_SMALL_MODEL,
        max_tokens=settings.LLM_SMALL_MAX_TOKENS,
        temperature=settings.LLM_SMALL_TEMPERATURE,
        timeout=settings.LLM_SMALL_TIMEOUT,
    )


async def close_llm_client() -> None:
    """关闭全局 LLMClient 单例并释放引用。"""
    global _llm_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None


async def close_llm_small_client() -> None:
    """关闭全局 small LLMClient 单例并释放引用。"""
    global _llm_small_client
    if _llm_small_client:
        await _llm_small_client.close()
        _llm_small_client = None


def get_llm_client() -> LLMClient:
    """
    获取已初始化的 main LLMClient 实例。

    :raises ValueError: 若尚未调用 init_llm_client()
    """
    if _llm_client is None:
        raise ValueError("LLMClient 未初始化，请先调用 init_llm_client()")
    return _llm_client


def get_llm_small_client() -> LLMClient:
    """
    获取已初始化的 small LLMClient 实例。

    :raises ValueError: 若尚未调用 init_llm_small_client()
    """
    if _llm_small_client is None:
        raise ValueError("LLMClient(small) 未初始化，请先调用 init_llm_small_client()")
    return _llm_small_client
