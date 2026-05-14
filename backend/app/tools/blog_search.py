"""博客检索工具定义。

此模块仅提供工具的 schema（供 LLM bind_tools 使用），
实际的数据库检索逻辑在 chat_graph.py 的 tools 节点中执行。
"""

from langchain_core.tools import tool


@tool
async def search_blog(query: str) -> str:
    """根据用户查询检索语义最相似的博客文章。

    当用户询问博客、文章、作者写的技术内容、学习笔记等相关问题时调用。
    输入应为用户的原始问题或关键词，输出为最相关的博客文章片段。

    Args:
        query: 用户的搜索关键词或问题描述
    """
    # 实际执行逻辑位于 app/graphs/chat_graph.py 的 tools 节点中。
    # 此函数仅用于生成 OpenAI 格式的 tool schema。
    return ""
