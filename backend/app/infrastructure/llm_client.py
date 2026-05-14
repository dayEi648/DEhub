from langchain_openai import ChatOpenAI

from app.core.config import settings

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
