from app.core.config import settings
from langchain_openai import ChatOpenAI
from langchain_openai.chat_models.base import (
    _convert_dict_to_message as _original_convert_dict_to_message,
    _convert_delta_to_message_chunk as _original_convert_delta_to_message_chunk,
    _convert_message_to_dict as _original_convert_message_to_dict,
)
from langchain_core.messages import AIMessage, AIMessageChunk


# =============================================================================
# Monkey-patch: 让 ChatOpenAI 支持 DeepSeek / 阿里云百炼等 OpenAI 兼容接口
# 的 reasoning_content 字段（thinking 模式）。
# =============================================================================

def _patched_convert_dict_to_message(_dict):
    """在接收非流式响应时，提取 reasoning_content 到 AIMessage.additional_kwargs。"""
    result = _original_convert_dict_to_message(_dict)
    if isinstance(result, AIMessage):
        reasoning = _dict.get("reasoning_content")
        if reasoning is not None:
            result.additional_kwargs["reasoning_content"] = reasoning
    return result


def _patched_convert_delta_to_message_chunk(_dict, default_class):
    """在接收流式响应时，提取 reasoning_content 到 AIMessageChunk.additional_kwargs。"""
    result = _original_convert_delta_to_message_chunk(_dict, default_class)
    if isinstance(result, AIMessageChunk):
        reasoning = _dict.get("reasoning_content")
        if reasoning is not None:
            result.additional_kwargs["reasoning_content"] = reasoning
    return result


def _patched_convert_message_to_dict(message, api="chat/completions"):
    """在发送请求时，将 AIMessage.additional_kwargs 中的 reasoning_content 回传给 API。"""
    result = _original_convert_message_to_dict(message, api=api)
    if isinstance(message, AIMessage) and "reasoning_content" in message.additional_kwargs:
        result["reasoning_content"] = message.additional_kwargs["reasoning_content"]
    return result


# 应用补丁
import langchain_openai.chat_models.base as _lc_openai_base

_lc_openai_base._convert_dict_to_message = _patched_convert_dict_to_message
_lc_openai_base._convert_delta_to_message_chunk = _patched_convert_delta_to_message_chunk
_lc_openai_base._convert_message_to_dict = _patched_convert_message_to_dict


# =============================================================================
# LLM Client
# =============================================================================

_llm_client: ChatOpenAI | None = None
_llm_small_client: ChatOpenAI | None = None


def _normalize_base_url(url: str) -> str:
    """确保 OpenAI 兼容 base_url 以 /v1 结尾。"""
    url = url.rstrip("/")
    if not url.endswith("/v1"):
        url = url + "/v1"
    return url


async def init_llm_client() -> None:
    """初始化全局主模型单例。"""
    global _llm_client
    _llm_client = ChatOpenAI(
        api_key=settings.LLM_MAIN_API_KEY,
        base_url=_normalize_base_url(settings.LLM_MAIN_BASE_URL),
        model=settings.LLM_MAIN_MODEL,
        max_tokens=settings.LLM_MAIN_MAX_TOKENS,
        temperature=settings.LLM_MAIN_TEMPERATURE,
        timeout=settings.LLM_MAIN_TIMEOUT,
        streaming=True,
    )


async def init_llm_small_client() -> None:
    """初始化全局小模型单例。"""
    global _llm_small_client
    _llm_small_client = ChatOpenAI(
        api_key=settings.LLM_SMALL_API_KEY,
        base_url=_normalize_base_url(settings.LLM_SMALL_BASE_URL),
        model=settings.LLM_SMALL_MODEL,
        max_tokens=settings.LLM_SMALL_MAX_TOKENS,
        temperature=settings.LLM_SMALL_TEMPERATURE,
        timeout=settings.LLM_SMALL_TIMEOUT,
    )


def get_llm_client() -> ChatOpenAI:
    """获取已初始化的主模型 ChatOpenAI 实例。"""
    if _llm_client is None:
        raise ValueError("LLM Client 未初始化")
    return _llm_client


def get_llm_small_client() -> ChatOpenAI:
    """获取已初始化的小模型 ChatOpenAI 实例。"""
    if _llm_small_client is None:
        raise ValueError("SMALL LLM Client 未初始化")
    return _llm_small_client


def close_llm_client() -> None:
    """释放全局主模型单例引用。"""
    global _llm_client
    _llm_client = None


def close_llm_small_client() -> None:
    """释放全局小模型单例引用。"""
    global _llm_small_client
    _llm_small_client = None
