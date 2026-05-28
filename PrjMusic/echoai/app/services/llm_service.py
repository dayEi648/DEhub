"""
LLM 服务封装。
基于 langchain-openai.ChatOpenAI，对接阿里云百炼兼容接口。
提供非流式和流式对话能力。
"""
from collections.abc import AsyncIterator

from langchain_core.messages import BaseMessage, AIMessageChunk
from langchain_openai import ChatOpenAI

from app.config import settings


class LLMService:
    """大语言模型服务封装。"""

    def __init__(self):
        self._llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            temperature=0.7,
            streaming=False,
        )
        self._llm_stream = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            temperature=0.7,
            streaming=True,
        )

    async def achat(self, messages: list[BaseMessage]) -> str:
        """
        非流式对话，返回完整回复文本。

        :param messages: LangChain 消息列表
        :return: AI 回复文本
        :raises LLMError: 调用失败时抛出
        """
        try:
            response = await self._llm.ainvoke(messages)
            return str(response.content)
        except Exception as e:
            raise LLMError(f"LLM 调用失败: {e}") from e

    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[str]:
        """
        流式对话，逐字返回内容块。

        :param messages: LangChain 消息列表
        :yields: 每个内容片段（字符串）
        :raises LLMError: 调用失败时抛出
        """
        try:
            async for chunk in self._llm_stream.astream(messages):
                if isinstance(chunk, AIMessageChunk):
                    text = chunk.content
                else:
                    text = str(chunk.content) if hasattr(chunk, "content") else str(chunk)
                if text:
                    yield text
        except Exception as e:
            raise LLMError(f"LLM 流式调用失败: {e}") from e


class LLMError(Exception):
    """LLM 调用异常。"""

    pass


# 全局单例
llm_service = LLMService()
