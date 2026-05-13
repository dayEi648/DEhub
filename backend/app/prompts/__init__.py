"""
系统提示词（System Prompts）集中管理模块。

按业务域拆分为子模块，避免单文件膨胀。
"""

from app.prompts.chat_prompts import (
    CONVERSATION_SUMMARY,
    DEFAULT_SYSTEM,
    MEMORY_REFERENCE_HEADER,
    MEMORY_SUMMARY_LABEL,
    MEMORY_TURN_LABEL,
    TITLE_GENERATION,
)

__all__ = [
    "CONVERSATION_SUMMARY",
    "DEFAULT_SYSTEM",
    "MEMORY_REFERENCE_HEADER",
    "MEMORY_SUMMARY_LABEL",
    "MEMORY_TURN_LABEL",
    "TITLE_GENERATION",
]
