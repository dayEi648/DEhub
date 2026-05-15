from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


_embedding_client: OpenAIEmbeddings | None = None


async def init_embedding_client() -> None:
    """初始化全局 Embedding 单例。"""
    global _embedding_client
    kwargs = {
        "api_key": settings.EMBEDDING_API_KEY,
        "base_url": settings.EMBEDDING_BASE_URL,
        "model": settings.EMBEDDING_MODEL,
        "chunk_size": 25,  # 阿里云百炼 text-embedding-v4 单次上限
    }
    if settings.EMBEDDING_DIMENSION is not None:
        kwargs["dimensions"] = settings.EMBEDDING_DIMENSION
    _embedding_client = OpenAIEmbeddings(**kwargs)


def get_embedding_client() -> OpenAIEmbeddings:
    """获取已初始化的 Embedding 实例。"""
    if _embedding_client is None:
        raise ValueError("EmbeddingClient 未初始化")
    return _embedding_client


async def close_embedding_client() -> None:
    """释放全局 Embedding 单例引用。"""
    global _embedding_client
    _embedding_client = None
