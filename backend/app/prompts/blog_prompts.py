# ===================================================================
# Blog Post Prompts（博客文章 AI 辅助提示词）
# ===================================================================

# -------------------------------------------------------------------
# 长文摘要生成（small model 用）
# -------------------------------------------------------------------
BLOG_SUMMARY_SYSTEM_PROMPT = (
    "你是一位专业的技术博客编辑，擅长提炼文章要点并撰写详尽的摘要。"
)

_BLOG_SUMMARY_USER_PROMPT_TEMPLATE = (
    "请根据以下 Markdown 格式的文章正文，生成一段 {min_length}~{max_length} 字的中文摘要。"
    "摘要应准确概括文章核心内容、关键观点和重要结论，语言简洁流畅，"
    "不要包含 Markdown 标记。只输出摘要正文，不要添加任何前缀、标题或解释。\n\n"
    "{content_md}"
)


def render_blog_summary_prompt(
    content_md: str,
    min_length: int,
    max_length: int,
) -> tuple[str, str]:
    """渲染博客长文摘要生成的 prompt。"""
    user_prompt = _BLOG_SUMMARY_USER_PROMPT_TEMPLATE.format(
        min_length=min_length,
        max_length=max_length,
        content_md=content_md,
    )
    return BLOG_SUMMARY_SYSTEM_PROMPT, user_prompt
