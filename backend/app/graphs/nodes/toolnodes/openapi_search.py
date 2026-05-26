"""OpenAPI 知识库检索工具定义（管理员专用）。

提供 search_openapi_docs Tool 的 schema 与完整执行逻辑。
该工具仅对管理员可见，普通用户无法通过任何途径触发。
"""

import logging

from langchain_core.tools import ToolException, tool

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.openapi_embedding_service import OpenAPIEmbeddingService

logger = logging.getLogger(__name__)


@tool
def search_openapi_docs(query: str) -> str:
    """
    检索已上传的 OpenAPI 文档知识库，回答接口相关问题。

    该工具仅对管理员可见。当管理员询问以下问题时调用：
    - 某个 API 接口的参数、返回值、使用方式
    - 系统内部接口的 path、method、请求体结构
    - "这个接口怎么调"、"参数是什么"、"返回什么"

    非触发条件（禁止调用）：
    - 用户未询问任何与 API 接口相关的问题
    - 用户询问的是博客内容、论坛话题、闲聊
    - 用户询问公开技术知识（应使用 search_blog 或 search_web）

    约束：
    - 如果知识库中没有相关文档，明确说明"当前知识库未找到相关接口"
    - 不得编造不存在的参数、路径、请求体或响应体
    - 返回内容必须是模型可读的摘要文本，不直接暴露复杂原始 JSON

    Args:
        query: 用户的搜索关键词或问题描述，如"用户登录接口"
    Returns:
        str: 格式化后的相关 API 端点信息，包含路径、方法、摘要、参数、响应。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = SessionLocal()
    try:
        service = OpenAPIEmbeddingService(db)
        results = service.search(
            query.strip(),
            top_k=5,
            min_similarity=settings.RAG_MIN_SIMILARITY,
        )

        if not results:
            return "当前知识库未找到相关接口。"

        parts = []
        for result in results:
            lines = [
                f"【API 端点】{result['method']} {result['path']}",
            ]
            if result.get("summary"):
                lines.append(f"摘要：{result['summary']}")
            if result.get("description"):
                lines.append(f"描述：{result['description']}")
            if result.get("operation_id"):
                lines.append(f"operationId：{result['operation_id']}")
            if result.get("tags"):
                lines.append(f"标签：{', '.join(result['tags'])}")
            lines.append(f"相似度：{result['similarity_score']:.4f}")
            # content 包含完整的端点文本，只展示前几行避免过长
            content_preview = "\n".join(result["content"].split("\n")[:8])
            lines.append(f"详情：\n{content_preview}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
    except Exception as exc:
        logger.exception("OpenAPI 知识库检索失败")
        raise ToolException("OpenAPI 知识库检索服务暂时不可用。") from exc
    finally:
        db.close()
