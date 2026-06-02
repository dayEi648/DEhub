# ===================================================================
# RAG Prompts（检索增强生成相关提示词）
# ===================================================================

# -------------------------------------------------------------------
# 博客查询改写 / Query Expansion（small model 用）
# -------------------------------------------------------------------
BLOG_QUERY_EXPANSION_SYSTEM_PROMPT = (
    "你是一位信息检索专家，擅长将用户口语化的查询改写为多条精准、专业的检索关键词。"
)

_BLOG_QUERY_EXPANSION_USER_TEMPLATE = (
    "请根据用户的原始查询，生成 {num_queries} 条语义等价但表述不同的检索查询。\n\n"
    "改写角度要求（每条覆盖不同角度）：\n"
    "1. 直接关键词提取：去除口语化、寒暄和废话，保留最精炼的核心概念\n"
    "2. 技术术语对齐：将口语化、模糊表达转为标准技术术语\n"
    "3. 意图扩展：基于核心概念扩展相关技术栈、应用场景或上下游概念\n"
    "4. 问题形式：将陈述转为技术问答形式，匹配博客文章标题风格\n"
    "5. 同义替换：使用同义词、近义词或不同技术社区常用说法重新表述\n\n"
    "规则：\n"
    "- 每条查询不超过 30 字\n"
    "- 必须保留原始查询的核心意图\n"
    "- 只输出改写后的查询文本，每行一条，不要编号、不要解释、不要加引号\n"
    "- 如果原始查询本身已经很精炼，可以适当重复但保持表述差异\n\n"
    "原始查询：{query}\n"
)


def render_blog_query_expansion_prompt(
    query: str, num_queries: int = 5
) -> tuple[str, str]:
    """渲染博客查询改写的 prompt。

    Args:
        query: 用户原始查询
        num_queries: 期望生成的改写查询数量

    Returns:
        tuple[str, str]: (system_prompt, user_prompt)
    """
    user_prompt = _BLOG_QUERY_EXPANSION_USER_TEMPLATE.format(
        num_queries=num_queries,
        query=query,
    )
    return BLOG_QUERY_EXPANSION_SYSTEM_PROMPT, user_prompt
