"""
Embedding 服务封装。
基于 langchain-openai.OpenAIEmbeddings，对接阿里云百炼 text-embedding-v4。
"""
from langchain_openai import OpenAIEmbeddings

from app.config import settings


class EmbeddingService:
    """文本嵌入服务封装。"""

    def __init__(self):
        self._embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
            dimensions=settings.embedding_dimension,
            check_embedding_ctx_length=False,
        )

    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        批量文本嵌入。

        :param texts: 文本列表
        :return: 向量列表，每个向量维度为 settings.embedding_dimension
        :raises EmbeddingError: 调用失败时抛出
        """
        if not texts:
            return []
        try:
            return await self._embeddings.aembed_documents(texts)
        except Exception as e:
            raise EmbeddingError(f"Embedding 批量调用失败: {e}") from e

    async def aembed_query(self, text: str) -> list[float]:
        """
        单条查询文本嵌入。

        :param text: 查询文本
        :return: 向量，维度为 settings.embedding_dimension
        :raises EmbeddingError: 调用失败时抛出
        """
        try:
            return await self._embeddings.aembed_query(text)
        except Exception as e:
            raise EmbeddingError(f"Embedding 查询调用失败: {e}") from e


class EmbeddingError(Exception):
    """Embedding 调用异常。"""

    pass


# 全局单例
embedding_service = EmbeddingService()
