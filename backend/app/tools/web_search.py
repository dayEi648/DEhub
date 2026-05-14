"""联网搜索工具定义。

此模块仅提供工具的 schema（供 LLM bind_tools 使用），
实际的 IQS 搜索调用逻辑在 chat_graph.py 的 tools 节点中执行。
"""

from langchain_core.tools import tool


@tool
async def search_web(query: str) -> str:
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
    # 实际执行逻辑位于 app/graphs/chat_graph.py 的 tools 节点中。
    # 此函数仅用于生成 OpenAI 格式的 tool schema。
    return ""
