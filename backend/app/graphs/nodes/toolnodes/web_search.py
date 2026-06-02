"""联网搜索工具定义。

提供 search_web Tool 的 schema 与完整执行逻辑。
支持 query 扩展、并行搜索、结果去重与格式化输出。
"""

import asyncio
import difflib
import json
import logging
import re

import httpx
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from app.core.config import settings
from app.infrastructure.llm_client import create_llm_small_client
from app.prompts.chat_prompts import render_web_search_expansion_prompt

logger = logging.getLogger(__name__)

_LABEL = "【搜索结果】"
_DEDUP_SIMILARITY_THRESHOLD = 0.85


# ------------------------------------------------------------------
# Query 扩展
# ------------------------------------------------------------------

def _extract_json_array(text: str) -> list[str] | None:
    """从文本中提取 JSON 字符串数组。

    处理 small 模型可能返回的 markdown 代码块、多余文字等情况。
    """
    if not text:
        return None

    # 1. 尝试先提取 ```json ... ``` 或 ``` ... ``` 中的内容
    code_block_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if code_block_match:
        candidate = code_block_match.group(1)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    # 2. 尝试在整个文本中找第一个 [ ... ] 结构
    bracket_match = re.search(r"(\[.*?\])", text, re.DOTALL)
    if bracket_match:
        candidate = bracket_match.group(1)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    # 3. 尝试将整段文本作为 JSON 解析
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list) and all(isinstance(q, str) for q in parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    return None


async def _expand_search_queries(original_query: str) -> list[str]:
    """调用 small 模型将原始 query 扩展为多个不同角度的搜索 query。

    降级策略：small 模型调用失败或 JSON 解析失败时，返回 [original_query]。
    """
    try:
        client = create_llm_small_client(
            timeout=settings.WEB_SEARCH_QUERY_EXPANSION_TIMEOUT
        )
        prompt = render_web_search_expansion_prompt(original_query)
        response = await client.ainvoke([HumanMessage(content=prompt)])

        content = response.content
        if isinstance(content, list):
            # 某些模型可能返回 content 为 list
            content = "".join(str(c) for c in content)

        expanded = _extract_json_array(str(content) if content else "")
        if expanded and len(expanded) > 0:
            # 过滤空字符串并去重，同时保留顺序
            seen: set[str] = set()
            unique_queries: list[str] = []
            for q in expanded:
                q = q.strip()
                if q and q not in seen:
                    seen.add(q)
                    unique_queries.append(q)
            if unique_queries:
                return unique_queries
    except Exception:
        logger.exception("Query 扩展失败，降级为原始 query")

    return [original_query]


# ------------------------------------------------------------------
# IQS 搜索
# ------------------------------------------------------------------

async def _iqs_search_single(query: str) -> list[dict]:
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
        "numResults": settings.IQS_NUM_RESULTS_PER_QUERY,
        "contents": {
            "mainText": False,
            "markdownText": False,
            "richMainBody": False,
            "summary": True,
            "rerankScore": True,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=settings.IQS_TIMEOUT) as client:
            resp = await client.post(
                settings.IQS_ENDPOINT, headers=headers, json=payload
            )
        resp.raise_for_status()
        data = resp.json()
        return data.get("pageItems", [])
    except Exception:
        logger.exception("IQS search failed for query: %s", query)
        return []


# ------------------------------------------------------------------
# 结果去重
# ------------------------------------------------------------------

def _get_result_text(item: dict) -> str:
    """提取用于相似度比较的结果文本。"""
    title = item.get("title", "")
    summary = item.get("summary", "")
    snippet = item.get("snippet", "")
    body = summary if summary else snippet
    return f"{title}\n{body}"


def _deduplicate_results(results: list[dict]) -> list[dict]:
    """对搜索结果进行两层去重：URL 去重 + 内容相似去重。"""
    if not results:
        return []

    # 第一层：URL 去重，保留先出现的
    url_seen: set[str] = set()
    url_deduped: list[dict] = []
    for item in results:
        link = item.get("link", "")
        if link and link in url_seen:
            continue
        if link:
            url_seen.add(link)
        url_deduped.append(item)

    # 第二层：内容相似去重
    final: list[dict] = []
    for item in url_deduped:
        text = _get_result_text(item)
        is_duplicate = False
        for existing in final:
            existing_text = _get_result_text(existing)
            similarity = difflib.SequenceMatcher(None, text, existing_text).ratio()
            if similarity >= _DEDUP_SIMILARITY_THRESHOLD:
                # 保留 rerankScore 更高的结果
                existing_score = existing.get("rerankScore", 0) or 0
                current_score = item.get("rerankScore", 0) or 0
                if current_score > existing_score:
                    # 替换为当前结果
                    final[final.index(existing)] = item
                is_duplicate = True
                break
        if not is_duplicate:
            final.append(item)

    return final


# ------------------------------------------------------------------
# 结果格式化
# ------------------------------------------------------------------

def _format_web_search_results(results: list[dict]) -> str:
    """将 IQS pageItems 列表格式化为结构化文本块。"""
    if not results:
        return "未找到相关网络搜索结果。"

    lines: list[str] = []
    for item in results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        summary = item.get("summary", "")
        link = item.get("link", "")
        hostname = item.get("hostname", "")

        # 摘要优先级：summary > snippet
        abstract = summary if summary else snippet

        parts = [f"{_LABEL} {title}"]
        if hostname:
            parts.append(f"来源：{hostname}")
        if abstract:
            parts.append(abstract)
        if link:
            parts.append(f"链接：{link}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


# ------------------------------------------------------------------
# Tool 入口
# ------------------------------------------------------------------

@tool
async def search_web(query: str) -> str:
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
        str: 格式化后的相关网络搜索结果，包含标题、来源、摘要、链接。
    """
    if not query or not query.strip():
        return "未提供有效的搜索关键词。"

    if not settings.IQS_API_KEY:
        logger.error("IQS_API_KEY 未配置")
        return "联网搜索服务暂时不可用。"

    try:
        # 1. 扩展 query
        queries = await _expand_search_queries(query.strip())
        logger.debug("Query 扩展结果: %s", queries)

        # 2. 并行搜索
        search_tasks = [_iqs_search_single(q) for q in queries]
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)

        # 3. 合并结果（过滤掉异常）
        all_results: list[dict] = []
        for result in search_results_list:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.warning("某个子 query 搜索失败: %s", result)

        # 4. 去重
        deduped = _deduplicate_results(all_results)

        # 5. 格式化返回
        return _format_web_search_results(deduped)
    except Exception:
        logger.exception("联网搜索执行失败")
        return "联网搜索服务暂时不可用。"
