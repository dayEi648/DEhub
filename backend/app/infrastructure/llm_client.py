from app.core.config import settings
from app.infrastructure._utils import normalize_openai_base_url
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek

# =============================================================================
# LLM Client
# =============================================================================

_llm_client: ChatDeepSeek | None = None
_llm_small_client: ChatOpenAI | None = None


async def init_llm_client() -> None:
    """初始化全局主模型单例。"""
    global _llm_client
    _llm_client = ChatDeepSeek(
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


def get_llm_client() -> ChatDeepSeek:
    """获取已初始化的主模型 ChatDeepSeek 实例。"""
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
