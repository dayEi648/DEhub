"""文本处理工具模块

提供 Markdown 清洗、纯文本提取等通用文本处理能力。
"""

import re


def extract_plain_text_summary(content_md: str, max_length: int = 120) -> str:
    """从 Markdown 正文中提取一段纯文本摘要。

    处理流程：
    1. 移除代码块、行内代码
    2. 移除图片、保留链接文本
    3. 移除标题标记、粗体、斜体、列表标记、引用标记
    4. 移除 HTML 标签、水平分割线、表格分隔符
    5. 压缩空白字符并截取指定长度

    Args:
        content_md: Markdown 格式正文
        max_length: 摘要最大长度（不含省略号）

    Returns:
        纯文本摘要。若正文清洗后为空则返回空字符串。
    """
    if not content_md or not isinstance(content_md, str):
        return ""

    text = content_md
    # 代码块
    text = re.sub(r"```[\s\S]*?```", "\n", text)
    # 行内代码
    text = re.sub(r"`[^`]*`", "", text)
    # 图片
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    # 链接：保留文本
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    # 标题标记
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # 粗体、斜体
    text = re.sub(r"\*\*|__|\*|_", "", text)
    # 无序列表
    text = re.sub(r"^[\*\-\+]\s+", "", text, flags=re.MULTILINE)
    # 有序列表
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    # 引用
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # 水平分割线
    text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.MULTILINE)
    # HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    # 表格分隔符
    text = re.sub(r"\|", " ", text)
    # 压缩空白
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if len(text) > max_length:
        text = text[:max_length] + "…"
    return text
