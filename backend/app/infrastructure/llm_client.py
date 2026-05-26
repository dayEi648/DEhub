import threading

from app.core.config import settings
from app.infrastructure._utils import normalize_openai_base_url
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, AIMessageChunk


# =============================================================================
# Monkey-patch: 让 ChatOpenAI 支持 DeepSeek / 阿里云百炼等 OpenAI 兼容接口
# 的 reasoning_content 字段（thinking 模式）。
#
# 注意：这是临时 workaround，依赖 langchain-openai 的内部私有函数。
# 当上游原生支持 reasoning_content 后应移除。
# =============================================================================

_patch_applied = False
_patch_lock = threading.Lock()


def _apply_deepseek_patch() -> None:
    """在首次初始化 LLM 时应用 DeepSeek reasoning_content 补丁（线程安全，仅执行一次）。"""
    global _patch_applied
    if _patch_applied:
        return
    with _patch_lock:
        if _patch_applied:
            return
        from langchain_openai.chat_models.base import (
            _convert_dict_to_message as _original_convert_dict_to_message,
            _convert_delta_to_message_chunk as _original_convert_delta_to_message_chunk,
            _convert_message_to_dict as _original_convert_message_to_dict,
        )
        import langchain_openai.chat_models.base as _lc_openai_base

        def _patched_convert_dict_to_message(_dict):
            result = _original_convert_dict_to_message(_dict)
            if isinstance(result, AIMessage):
                reasoning = _dict.get("reasoning_content")
                if reasoning is not None:
                    result.additional_kwargs["reasoning_content"] = reasoning
            return result

        def _patched_convert_delta_to_message_chunk(_dict, default_class):
            result = _original_convert_delta_to_message_chunk(_dict, default_class)
            if isinstance(result, AIMessageChunk):
                reasoning = _dict.get("reasoning_content")
                if reasoning is not None:
                    result.additional_kwargs["reasoning_content"] = reasoning
            return result

        def _patched_convert_message_to_dict(message, api="chat/completions"):
            result = _original_convert_message_to_dict(message, api=api)
            if isinstance(message, AIMessage) and "reasoning_content" in message.additional_kwargs:
                result["reasoning_content"] = message.additional_kwargs["reasoning_content"]
            return result

        _lc_openai_base._convert_dict_to_message = _patched_convert_dict_to_message
        _lc_openai_base._convert_delta_to_message_chunk = _patched_convert_delta_to_message_chunk
        _lc_openai_base._convert_message_to_dict = _patched_convert_message_to_dict
        _patch_applied = True


# =============================================================================
# LLM Client
# =============================================================================

_llm_client: ChatOpenAI | None = None
_llm_small_client: ChatOpenAI | None = None


async def init_llm_client() -> None:
    """初始化全局主模型单例。"""
    _apply_deepseek_patch()
    global _llm_client
    _llm_client = ChatOpenAI(
        api_key=settings.LLM_MAIN_API_KEY,
        base_url=normalize_openai_base_url(settings.LLM_MAIN_BASE_URL),
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
        base_url=normalize_openai_base_url(settings.LLM_SMALL_BASE_URL),
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


def create_llm_small_client(timeout: int | None = None) -> ChatOpenAI:
    """
    创建一个临时的小模型 ChatOpenAI 实例，可覆盖 timeout。
    用于需要比全局单例更长/更短超时时间的场景（如长文摘要生成）。
    """
    return ChatOpenAI(
        api_key=settings.LLM_SMALL_API_KEY,
        base_url=normalize_openai_base_url(settings.LLM_SMALL_BASE_URL),
        model=settings.LLM_SMALL_MODEL,
        max_tokens=settings.LLM_SMALL_MAX_TOKENS,
        temperature=settings.LLM_SMALL_TEMPERATURE,
        timeout=timeout if timeout is not None else settings.LLM_SMALL_TIMEOUT,
    )


def close_llm_client() -> None:
    """释放全局主模型单例引用。"""
    global _llm_client
    _llm_client = None


def close_llm_small_client() -> None:
    """释放全局小模型单例引用。"""
    global _llm_small_client
    _llm_small_client = None
