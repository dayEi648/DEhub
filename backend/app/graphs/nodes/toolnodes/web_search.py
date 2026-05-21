"""联网搜索工具定义。

提供 search_web Tool 的 schema 与完整执行逻辑。
支持单次搜索与结果格式化输出。
"""

import logging

import httpx
from langchain_core.tools import tool

from app.core.config import settings

logger = logging.getLogger(__name__)

_LABEL = "【搜索结果】"


def _iqs_search_single(query: str) -> list[dict]:
    """对单个 query 调用阿里云 IQS Search，返回 pageItems 列表。"""
    api_key = settings.IQS_API_KEY
    if not api_key:
        logger.error("IQS API key is not set")
        return []

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "engineType": "Generic",
        "numResults": settings.IQS_NUM_RESULTS,
        "contents": {
            "mainText": False,
            "markdownText": True,
            "richMainBody": False,
            "summary": False,
            "rerankScore": True,
        },
    }

    try:
        with httpx.Client(timeout=settings.IQS_TIMEOUT) as client:
            resp = client.post(
                settings.IQS_ENDPOINT, headers=headers, json=payload
            )
        resp.raise_for_status()
        data = resp.json()
        return data.get("pageItems", [])
    except Exception as e:
        logger.error("IQS search failed: %s", e)
        return []


def _format_web_search_results(results: list[dict]) -> str:
    """将 IQS pageItems 列表格式化为结构化文本块。"""
    if not results:
        return "未找到相关网络搜索结果。"

    lines: list[str] = []
    for item in results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        markdown_text = item.get("markdownText", "")
        link = item.get("link", "")
        hostname = item.get("hostname", "")

        parts = [f"{_LABEL} {title}"]
        if hostname:
            parts.append(f"来源：{hostname}")
        if markdown_text:
            parts.append(markdown_text)
        elif snippet:
            parts.append(snippet)
        if link:
            parts.append(f"链接：{link}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


@tool
def search_web(query: str) -> str:
    """
    使用联网搜索获取实时、时效性或超出内置知识范围的最新信息。

    当用户询问以下情况时调用：
    - 时事新闻、最新技术动态、股价、天气等强时效性内容
    - 超出你训练数据截止日期的最新技术、产品、政策动态
    - 用户明确要求"搜索一下"、"上网查"、"联网搜索"
    - 你不确定答案或知识可能已过时

    Args:
        query: 用户的搜索关键词或问题描述
    Returns:
        str: 格式化后的相关网络搜索结果，包含标题、来源、正文（Markdown）、链接。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    if not settings.IQS_API_KEY:
        logger.error("IQS_API_KEY 未配置")
        return "联网搜索服务暂时不可用。"

    try:
        results = _iqs_search_single(query.strip())
        return _format_web_search_results(results)
    except Exception:
        logger.exception("联网搜索执行失败")
        return "联网搜索服务暂时不可用。"
