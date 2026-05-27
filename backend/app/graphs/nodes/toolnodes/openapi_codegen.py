"""OpenAPI 调用示例生成工具定义（管理员专用）。

提供 generate_openapi_call_example Tool 的 schema 与完整执行逻辑。
该工具仅对管理员可见，基于知识库检索结果生成接口调用示例。
"""

import logging

from langchain_core.tools import ToolException, tool

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.openapi_embedding_service import OpenAPIEmbeddingService

logger = logging.getLogger(__name__)

_MAX_CONTENT_CHARS_PER_RESULT = 2000


@tool
def generate_openapi_call_example(
    query: str,
    method: str | None = None,
    document_id: int | None = None,
) -> str:
    """
    基于已上传的 OpenAPI 文档知识库，生成接口调用示例代码。

    该工具仅对管理员可见。当管理员需要以下帮助时调用：
    - "给我写个调用示例"
    - "这个接口怎么用 Python/JS/curl 调用"
    - "生成请求代码"
    - 需要具体的 HTTP 请求示例

    非触发条件（禁止调用）：
    - 用户未要求生成代码示例
    - 用户询问的是接口定义而非调用方式
    - 非管理员对话（工具不可见）

    约束：
    - 如果知识库中没有相关文档，明确说明"当前知识库未找到相关接口，无法生成示例"
    - 不得编造不存在的参数、路径、请求体或响应体
    - 返回内容必须是模型可读的摘要文本，包含示例代码片段

    Args:
        query: 用户的搜索关键词或接口描述，如"用户登录接口调用示例"
        method: 可选，按 HTTP 方法过滤
        document_id: 可选，按文档 ID 过滤
    Returns:
        str: 格式化后的接口调用示例，包含端点信息和建议的代码结构。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    db = SessionLocal()
    try:
        service = OpenAPIEmbeddingService(db)
        results = service.search(
            query.strip(),
            top_k=settings.RAG_OPENAPI_CODEGEN_TOP_K,
            min_similarity=settings.RAG_MIN_SIMILARITY,
            method=method,
            document_id=document_id,
        )

        if not results:
            return "当前知识库未找到相关接口，无法生成示例。"

        parts = ["基于知识库中的以下接口，建议的调用示例：\n"]
        for result in results:
            method = result["method"]
            path = result["path"]
            summary = result.get("summary", "")
            content = result.get("content", "")

            lines = [
                f"【接口】{method} {path}",
            ]
            if summary:
                lines.append(f"摘要：{summary}")

            # 提取 content 中的参数和请求体信息（结构化展示）
            lines.append("\n调用结构参考：")
            lines.append(f"{method} {path}")
            # 展示 content 的关键行（请求体和响应体），并按长度预算真实截断
            truncated = False
            for line in content.split("\n"):
                if any(
                    k in line
                    for k in (
                        "Summary:",
                        "Description:",
                        "Request Body",
                        "Response",
                        "- ",
                    )
                ):
                    projected_len = sum(len(item) + 1 for item in lines) + len(line)
                    if projected_len > _MAX_CONTENT_CHARS_PER_RESULT:
                        truncated = True
                        break
                    lines.append(line)

            if truncated:
                lines.append("...（内容已截断）")

            lines.append(f"\n相似度：{result['similarity_score']:.4f}")
            parts.append("\n".join(lines))

        return "\n\n".join(parts)
    except Exception as exc:
        logger.exception("OpenAPI 调用示例生成失败")
        raise ToolException("OpenAPI 调用示例生成服务暂时不可用。") from exc
    finally:
        db.close()
