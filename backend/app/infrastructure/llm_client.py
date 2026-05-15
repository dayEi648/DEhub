from app.core.config import settings
from langchain_openai import ChatOpenAI


_llm_client: ChatOpenAI | None = None
_llm_small_client: ChatOpenAI | None = None


async def init_llm_client() -> None:
    """初始化全局主模型单例。"""
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
    """初始化全局小模型单例。"""
    global _llm_small_client
    _llm_small_client = ChatOpenAI(
        api_key=settings.LLM_SMALL_API_KEY,
        base_url=settings.LLM_SMALL_BASE_URL,
        model=settings.LLM_SMALL_MODEL,
        max_tokens=settings.LLM_SMALL_MAX_TOKENS,
        temperature=settings.LLM_SMALL_TEMPERATURE,
        timeout=settings.LLM_SMALL_TIMEOUT
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