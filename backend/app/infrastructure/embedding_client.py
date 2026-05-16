from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.infrastructure._utils import normalize_openai_base_url


_embedding_client: OpenAIEmbeddings | None = None


async def init_embedding_client() -> None:
    """初始化全局 Embedding 单例。"""
    global _embedding_client
    kwargs = {
        "api_key": settings.EMBEDDING_API_KEY,
        "base_url": normalize_openai_base_url(settings.EMBEDDING_BASE_URL),
        "model": settings.EMBEDDING_MODEL,
        "chunk_size": settings.EMBEDDING_CHUNK_SIZE,
        # 阿里云百炼兼容层不支持传入 token IDs（整数列表），
        # 必须直接传原始字符串，因此关闭上下文长度检查。
        "check_embedding_ctx_length": False,
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
