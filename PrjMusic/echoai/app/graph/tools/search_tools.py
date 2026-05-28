"""
IQS 联网搜索工具。
调用阿里云 IQS API 获取实时信息。
"""
import httpx

from app.config import settings


class WebSearchError(Exception):
    """联网搜索异常。"""

    pass


async def web_search(query: str, num_results: int = 5) -> list[dict]:
    """
    调用 IQS 联网搜索 API。

    :param query: 搜索关键词
    :param num_results: 返回结果数（默认 5）
    :return: 搜索结果列表，每条包含 title、snippet、link
    :raises WebSearchError: 调用失败
    """
    if not settings.iqs_api_key:
        raise WebSearchError("IQS API Key 未配置")

    headers = {
        "Authorization": f"Bearer {settings.iqs_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "engineType": "LiteAdvanced",
        "numResults": num_results,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                settings.iqs_endpoint,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise WebSearchError(f"IQS HTTP 错误: {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise WebSearchError(f"IQS 请求失败: {e}") from e
    except Exception as e:
        raise WebSearchError(f"IQS 调用异常: {e}") from e

    # 解析返回结果（适配 IQS 统一搜索响应格式）
    results = []
    items = data.get("data", {}).get("results", [])
    if not items and "results" in data:
        items = data.get("results", [])
    if not items and isinstance(data, list):
        items = data

    for item in items[:num_results]:
        results.append({
            "title": item.get("title", "") or item.get("name", ""),
            "snippet": item.get("snippet", "") or item.get("summary", "") or item.get("content", ""),
            "link": item.get("link", "") or item.get("url", ""),
        })

    return results
