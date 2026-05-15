"""联网搜索工具定义。

提供 search_web Tool 的 schema 与完整执行逻辑。
支持 query 拆分、并行搜索、结果合并去重排序与格式化。
"""

import asyncio
import logging
from typing import Annotated

import httpx
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from app.core.config import settings
from app.prompts.chat_prompts import WEB_SEARCH_LABEL, WEB_SEARCH_QUERY_SPLIT

logger = logging.getLogger(__name__)

_IQS_ENDPOINT = "https://cloud-iqs.aliyuncs.com/search/unified"
_IQS_TIMEOUT = 30


async def _iqs_search_single(query: str, api_key: str) -> list[dict]:
    """对单个 query 调用阿里云 IQS Search，返回 pageItems 列表。"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "engineType": "Generic",
        "numResults": 10,
        "contents": {
            "mainText": False,
            "markdownText": False,
            "richMainBody": False,
            "summary": False,
            "rerankScore": True,
        },
    }
    async with httpx.AsyncClient(timeout=_IQS_TIMEOUT) as client:
        resp = await client.post(_IQS_ENDPOINT, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("pageItems", [])


async def _split_search_queries(query: str, llm_small: BaseChatModel) -> list[str]:
    """使用 small LLM 将用户 query 拆分为 1~5 个搜索片段。"""
    try:
        msg = await llm_small.ainvoke(
            [
                SystemMessage(content=WEB_SEARCH_QUERY_SPLIT),
                HumanMessage(content=query),
            ]
        )
        lines = [line.strip() for line in (msg.content or "").splitlines() if line.strip()]
        return lines[:5] if lines else [query]
    except Exception:
        logger.warning("Query 拆分失败，回退到原始 query")
        return [query]


def _format_web_search_results(results: list[dict]) -> str:
    """将 IQS pageItems 列表格式化为文本块。"""
    if not results:
        return "未找到相关网络搜索结果。"

    lines: list[str] = []
    for item in results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        hostname = item.get("hostname", "")
        parts = [f"{WEB_SEARCH_LABEL} {title}"]
        if hostname:
            parts.append(f"来源：{hostname}")
        if snippet:
            parts.append(snippet)
        if link:
            parts.append(f"链接：{link}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


@tool
async def search_web(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """使用联网搜索获取实时、时效性或超出内置知识范围的最新信息。

    当用户询问以下情况时调用：
    - 当前时事、新闻、股价、天气、赛事结果等时效性信息
    - 超出你训练数据截止日期的最新技术、产品、政策动态
    - 用户明确要求"搜索一下"、"上网查"、"联网搜索"
    - 你不确定答案或知识可能已过时

    输入应为用户的原始问题或关键词，系统会自动将其拆分为多个搜索片段并行查询。

    Args:
        query: 用户的搜索关键词或问题描述
    """
    llm_small = config["configurable"].get("llm_small")
    if llm_small is None:
        logger.error("search_web 缺少 llm_small 依赖")
        return "联网搜索服务配置错误。"

    api_key = settings.IQS_API_KEY
    if not api_key:
        logger.error("IQS_API_KEY 未配置")
        return "联网搜索服务暂时不可用。"

    try:
        # 1. 拆分 query
        sub_queries = await _split_search_queries(query, llm_small)
        # 2. 并行搜索
        tasks = [_iqs_search_single(q, api_key) for q in sub_queries]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        # 3. 合并、去重、排序
        seen_links: set[str] = set()
        merged: list[dict] = []
        for items in raw_results:
            if isinstance(items, Exception):
                logger.warning("某条子查询搜索失败: %s", items)
                continue
            for item in items:
                link = item.get("link")
                if link and link not in seen_links:
                    seen_links.add(link)
                    merged.append(item)
        merged.sort(key=lambda x: x.get("rerankScore", 0), reverse=True)
        # 4. 格式化
        content = _format_web_search_results(merged)
        return content
    except Exception:
        logger.exception("联网搜索执行失败")
        return "联网搜索服务暂时不可用。"
