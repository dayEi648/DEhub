from langchain_openai import ChatOpenAI

from app.core.config import settings

# ------------------------------------------------------------------
# Monkey-patch: 支持 DeepSeek 等思考模型的 reasoning_content
# ------------------------------------------------------------------
# LangChain OpenAI 默认不提取/传递 reasoning_content，但 DeepSeek 等
# OpenAI 兼容 API 在 thinking 模式下要求后续请求必须原样传回该字段。
# 以下补丁在消息解析时提取 reasoning_content，在序列化时原样传回。
# ------------------------------------------------------------------

import langchain_openai.chat_models.base as _lc_openai_base

_original_convert_dict_to_message = _lc_openai_base._convert_dict_to_message


def _patched_convert_dict_to_message(_dict):
    role = _dict.get("role")
    if role == "assistant":
        reasoning_content = _dict.get("reasoning_content")
        if reasoning_content:
            msg = _original_convert_dict_to_message(_dict)
            msg.additional_kwargs["reasoning_content"] = reasoning_content
            return msg
    return _original_convert_dict_to_message(_dict)


_lc_openai_base._convert_dict_to_message = _patched_convert_dict_to_message

_original_convert_message_to_dict = _lc_openai_base._convert_message_to_dict


def _patched_convert_message_to_dict(message, api="chat/completions"):
    message_dict = _original_convert_message_to_dict(message, api)
    if (
        hasattr(message, "additional_kwargs")
        and "reasoning_content" in message.additional_kwargs
    ):
        message_dict["reasoning_content"] = message.additional_kwargs["reasoning_content"]
    return message_dict


_lc_openai_base._convert_message_to_dict = _patched_convert_message_to_dict

# ------------------------------------------------------------------
# 补充 patch：流式模式下 _convert_delta_to_message_chunk 同样需要
# 提取 reasoning_content，否则 astream 产生的 AIMessageChunk 会丢失该字段。
# merge_dicts 对字符串使用 += 累加，可将各 chunk 的 reasoning_content 增量
# 拼接为完整内容。
# ------------------------------------------------------------------

_original_convert_delta_to_message_chunk = (
    _lc_openai_base._convert_delta_to_message_chunk
)


def _patched_convert_delta_to_message_chunk(_dict, default_class):
    msg_chunk = _original_convert_delta_to_message_chunk(_dict, default_class)
    reasoning_content = _dict.get("reasoning_content")
    if reasoning_content and hasattr(msg_chunk, "additional_kwargs"):
        msg_chunk.additional_kwargs["reasoning_content"] = reasoning_content
    return msg_chunk


_lc_openai_base._convert_delta_to_message_chunk = _patched_convert_delta_to_message_chunk

_llm_client: ChatOpenAI | None = None
_llm_small_client: ChatOpenAI | None = None


async def init_llm_client() -> None:
    """初始化全局主模型 ChatOpenAI 单例。"""
    global _llm_client
    _llm_client = ChatOpenAI(
        api_key=settings.LLM_MAIN_API_KEY,
        base_url=settings.LLM_MAIN_BASE_URL,
        model=settings.LLM_MAIN_MODEL,
        max_tokens=settings.LLM_MAIN_MAX_TOKENS,
        temperature=settings.LLM_MAIN_TEMPERATURE,
        timeout=settings.LLM_MAIN_TIMEOUT,
        streaming=True,
    )


async def init_llm_small_client() -> None:
    """初始化全局小模型 ChatOpenAI 单例。"""
    global _llm_small_client
    _llm_small_client = ChatOpenAI(
        api_key=settings.LLM_SMALL_API_KEY,
        base_url=settings.LLM_SMALL_BASE_URL,
        model=settings.LLM_SMALL_MODEL,
        max_tokens=settings.LLM_SMALL_MAX_TOKENS,
        temperature=settings.LLM_SMALL_TEMPERATURE,
        timeout=settings.LLM_SMALL_TIMEOUT,
        streaming=True,
    )


async def close_llm_client() -> None:
    """释放全局主模型单例引用。"""
    global _llm_client
    _llm_client = None


async def close_llm_small_client() -> None:
    """释放全局小模型单例引用。"""
    global _llm_small_client
    _llm_small_client = None


def get_llm_client() -> ChatOpenAI:
    """
    获取已初始化的主模型 ChatOpenAI 实例。

    :raises ValueError: 若尚未调用 init_llm_client()
    """
    if _llm_client is None:
        raise ValueError("LLMClient 未初始化，请先调用 init_llm_client()")
    return _llm_client


def get_llm_small_client() -> ChatOpenAI:
    """
    获取已初始化的小模型 ChatOpenAI 实例。

    :raises ValueError: 若尚未调用 init_llm_small_client()
    """
    if _llm_small_client is None:
        raise ValueError("LLMClient(small) 未初始化，请先调用 init_llm_small_client()")
    return _llm_small_client
