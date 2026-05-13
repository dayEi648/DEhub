import asyncio
from typing import Any, AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from app.infrastructure.llm_client import LLMClient


class CustomChatModel(BaseChatModel):
    """
    将现有的异步 LLMClient 包装为 LangChain BaseChatModel。

    支持同步/异步非流式生成以及异步流式生成，
    使 LLMClient 能够无缝接入 LangGraph / LangChain 生态。
    """

    _client: LLMClient

    def __init__(self, client: LLMClient, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._client = client

    @property
    def _llm_type(self) -> str:
        return "custom_http"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"model": self._client._model}

    # ------------------------------------------------------------------
    # 消息格式转换
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_to_dict(messages: list[BaseMessage]) -> list[dict[str, str]]:
        """LangChain Message -> OpenAI 兼容 dict。"""
        result: list[dict[str, str]] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage) or isinstance(msg, AIMessageChunk):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "user"
            result.append({"role": role, "content": msg.content or ""})
        return result

    # ------------------------------------------------------------------
    # 同步生成（fallback，实际在 FastAPI 中不会被调用）
    # ------------------------------------------------------------------

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成入口。内部委托给异步的 _agenerate。"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._agenerate(messages, stop, run_manager, **kwargs))

        # 若当前已在事件循环中（如某些同步测试场景），在新线程中运行
        future = asyncio.run_coroutine_threadsafe(
            self._agenerate(messages, stop, run_manager, **kwargs), loop
        )
        return future.result()

    # ------------------------------------------------------------------
    # 异步生成
    # ------------------------------------------------------------------

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步非流式生成。"""
        messages_dict = self._convert_to_dict(messages)
        response_text = await self._client.achat(messages_dict)
        return ChatResult(
            generations=[
                ChatGeneration(message=AIMessage(content=response_text))
            ]
        )

    # ------------------------------------------------------------------
    # 异步流式生成
    # ------------------------------------------------------------------

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """异步流式生成，逐 token yield。"""
        messages_dict = self._convert_to_dict(messages)
        async for chunk_text in self._client.astream_chat(messages_dict):
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=chunk_text)
            )
