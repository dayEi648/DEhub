"""Slug 生成工具模块

提供将任意文本转换为 URL 安全 slug 的能力，并支持自动处理唯一性冲突。
"""

import re
import unicodedata
from typing import Callable

from sqlalchemy.orm import Session


def generate_slug(text: str) -> str:
    """将任意文本转换为 URL 安全的 slug。

    转换规则：
    1. 去除首尾空白，转为小写
    2. 将空格、下划线替换为连字符
    3. 保留字母、数字、中文字符、连字符
    4. 合并连续连字符
    5. 截断至 100 字符（预留空间给唯一性后缀）

    Args:
        text: 原始文本，如文章标题或分类名称

    Returns:
        URL 友好的 slug 字符串。若输入无效则返回 "untitled"

    Examples:
        >>> generate_slug("Hello World!")
        'hello-world'
        >>> generate_slug("  我的第一篇博客  ")
        '我的第一篇博客'
        >>> generate_slug("---a__b  c!!!---")
        'a-b-c'
    """
    if not text or not text.strip():
        return "untitled"

    # 1. 去除首尾空白，NFKC 规范化
    text = text.strip()
    text = unicodedata.normalize("NFKC", text)

    # 2. 转为小写（仅影响 ASCII 字母，中文字符不受影响）
    text = text.lower()

    # 3. 将空白字符、下划线替换为连字符
    text = re.sub(r"[\s_]+", "-", text)

    # 4. 保留：字母、数字、中文字符（\u4e00-\u9fff）、连字符
    #    移除其他所有字符（标点、特殊符号等）
    text = re.sub(r"[^\w\u4e00-\u9fff-]", "", text, flags=re.UNICODE)

    # 5. 合并连续连字符
    text = re.sub(r"-+", "-", text)

    # 6. 去除首尾连字符
    text = text.strip("-")

    # 7. 截断至 100 字符，避免过长 slug
    if len(text) > 100:
        text = text[:100].rstrip("-")

    return text if text else "untitled"


def generate_unique_slug(
    db: Session,
    text: str,
    *,
    exists_checker: Callable[[Session, str], object | None],
) -> str:
    """生成保证数据库唯一性的 slug。

    当基础 slug 已存在时，自动追加 "-1"、"-2" 等数字后缀，直到找到唯一值。

    Args:
        db: 数据库会话
        text: 原始文本，用于生成基础 slug
        exists_checker: 接收 (db, slug) 并返回对象（存在）或 None（不存在）的查询函数

    Returns:
        保证唯一的 slug 字符串

    Raises:
        ValueError: 若 exists_checker 不是可调用的函数
    """
    if not callable(exists_checker):
        raise ValueError("exists_checker must be a callable")

    base_slug = generate_slug(text)
    candidate = base_slug
    suffix = 1

    # 循环尝试，直到找到不存在的 slug
    # 设置安全上限，避免极端情况下的无限循环
    max_attempts = 1000
    for _ in range(max_attempts):
        existing = exists_checker(db, candidate)
        if existing is None:
            return candidate
        candidate = f"{base_slug}-{suffix}"
        suffix += 1

    # 理论上在正常使用中不会触发，作为兜底保护
    raise RuntimeError(
        f"Unable to generate a unique slug for base '{base_slug}' after {max_attempts} attempts"
    )
