import asyncio
import json
from typing import Any, AsyncIterator

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.runnables import RunnableBinding
from langchain_core.utils.function_calling import convert_to_openai_tool

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
    def _convert_to_dict(messages: list[BaseMessage]) -> list[dict[str, Any]]:
        """LangChain Message -> OpenAI 兼容 dict。"""
        result: list[dict[str, Any]] = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage) or isinstance(msg, AIMessageChunk):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, ToolMessage):
                role = "tool"
            else:
                role = "user"
            item: dict[str, Any] = {"role": role, "content": msg.content or ""}
            if isinstance(msg, ToolMessage):
                item["tool_call_id"] = msg.tool_call_id
            result.append(item)
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
        tools = kwargs.get("tools")
        if tools:
            content, tool_calls = await self._client.achat_with_tools(
                messages_dict,
                tools=tools,
                tool_choice=kwargs.get("tool_choice"),
            )
            lc_tool_calls = self._convert_openai_tool_calls_to_lc(tool_calls)
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content=content,
                            tool_calls=lc_tool_calls,
                        )
                    )
                ]
            )
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
        async for chunk_text in self._client.astream_chat(
            messages_dict,
            tools=kwargs.get("tools"),
            tool_choice=kwargs.get("tool_choice"),
        ):
            yield ChatGenerationChunk(
                message=AIMessageChunk(content=chunk_text)
            )

    # ------------------------------------------------------------------
    # Tool Calling 支持
    # ------------------------------------------------------------------

    def bind_tools(
        self,
        tools: list[Any],
        **kwargs: Any,
    ) -> RunnableBinding:
        """绑定工具 schema，使 LLM 可在生成时输出 tool_calls。"""
        openai_tools = [convert_to_openai_tool(t) for t in tools]
        return self.bind(tools=openai_tools, **kwargs)

    @staticmethod
    def _convert_openai_tool_calls_to_lc(tool_calls: list[dict]) -> list[dict]:
        """将 OpenAI API 返回的 tool_calls 转为 LangChain 内部格式。"""
        result: list[dict] = []
        for tc in tool_calls:
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}
            result.append(
                {
                    "id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "args": args,
                }
            )
        return result
