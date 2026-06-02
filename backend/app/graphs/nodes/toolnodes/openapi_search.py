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

_MAX_CONTENT_CHARS_PER_RESULT = 2000


@tool
def search_openapi_docs(
    query: str,
    method: str | None = None,
    document_id: int | None = None,
) -> str:
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
        method: 可选，按 HTTP 方法过滤，如 "GET" / "POST"
        document_id: 可选，按文档 ID 过滤，限定检索范围
    Returns:
        str: 格式化后的相关 API 端点信息，包含路径、方法、摘要、参数、响应。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = None
    try:
        db = SessionLocal()
        service = OpenAPIEmbeddingService(db)
        results = service.search(
            query.strip(),
            top_k=settings.RAG_OPENAPI_SEARCH_TOP_K,
            min_similarity=settings.RAG_MIN_SIMILARITY,
            method=method,
            document_id=document_id,
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
            # 按长度预算裁剪 content，避免过长导致上下文溢出
            content = result.get("content", "")
            if len(content) > _MAX_CONTENT_CHARS_PER_RESULT:
                content = content[:_MAX_CONTENT_CHARS_PER_RESULT] + "\n...（已截断）"
            lines.append(f"详情：\n{content}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
    except Exception as exc:
        logger.exception("OpenAPI 知识库检索失败")
        raise ToolException("OpenAPI 知识库检索服务暂时不可用。") from exc
    finally:
        if db:
            db.close()
