"""内容 sanitization 工具。

根据 AI 返回的敏感片段位置信息，对原文做确定性替换，
避免让 LLM 直接改写数据库内容。
"""

from __future__ import annotations

import logging
from typing import TypedDict

from app.schemas.content_moderation import FlaggedSpan

logger = logging.getLogger(__name__)


class SanitizationResult(TypedDict):
    """单字段替换结果。"""

    field: str
    original: str
    sanitized: str
    replaced_count: int
    failed_spans: list[dict]


def _mask_text(text: str, start: int, end: int) -> str:
    """将指定区间替换为等长 *。"""
    if start < 0 or end > len(text) or start >= end:
        return text
    mask = "*" * (end - start)
    return text[:start] + mask + text[end:]


def _apply_spans_to_field(field: str, text: str, spans: list[FlaggedSpan]) -> SanitizationResult:
    """对单个字段应用敏感片段替换。

    策略：
    1. 按 start 降序排序，从后往前替换，避免位置偏移。
    2. 对每个 span，先精确匹配 text[start:end] 是否等于 span.text。
    3. 精确匹配成功则替换；失败则尝试在字段内模糊查找 span.text。
    4. 模糊查找也失败则记录为 failed_span，不替换该片段。
    5. 如果有任何 span 失败，且成功替换数为 0，则降级为整字段替换为等长 *。
    """
    failed_spans: list[dict] = []
    replaced_count = 0
    current_text = text

    # 按 start 降序，从后往前替换
    sorted_spans = sorted(spans, key=lambda s: s.start, reverse=True)

    for span in sorted_spans:
        # 精确位置匹配
        if 0 <= span.start < span.end <= len(current_text):
            actual = current_text[span.start:span.end]
            if actual == span.text:
                current_text = _mask_text(current_text, span.start, span.end)
                replaced_count += 1
                continue

        # 模糊匹配：在字段中查找 span.text
        idx = current_text.find(span.text)
        if idx != -1:
            current_text = _mask_text(current_text, idx, idx + len(span.text))
            replaced_count += 1
            logger.warning(
                "Sanitizer 模糊匹配成功: field=%s, span_text=%r",
                field, span.text[:50]
            )
            continue

        # 匹配失败
        failed_spans.append({
            "field": field,
            "text": span.text,
            "start": span.start,
            "end": span.end,
            "reason": "文本片段在字段中无法定位",
        })
        logger.warning(
            "Sanitizer 匹配失败: field=%s, span_text=%r",
            field, span.text[:50]
        )

    # 降级策略：如果全部失败，整字段替换为等长 *
    if replaced_count == 0 and failed_spans:
        current_text = "*" * len(text)
        replaced_count = len(failed_spans)
        logger.warning(
            "Sanitizer 降级为整字段替换: field=%s, length=%d",
            field, len(text)
        )

    return SanitizationResult(
        field=field,
        original=text,
        sanitized=current_text,
        replaced_count=replaced_count,
        failed_spans=failed_spans,
    )


def sanitize_content(
    original_snapshot: dict[str, str],
    flagged_spans: list[FlaggedSpan],
) -> tuple[dict[str, str], list[SanitizationResult], list[dict]]:
    """根据敏感片段对内容做确定性替换。

    Args:
        original_snapshot: 原始字段快照。
        flagged_spans: 模型标出的敏感片段列表。

    Returns:
        (sanitized_snapshot, results, all_failed_spans)
        - sanitized_snapshot: 替换后的字段值映射
        - results: 每个字段的替换详情
        - all_failed_spans: 所有匹配失败的片段（用于记录 action_failed）
    """
    # 按字段分组
    spans_by_field: dict[str, list[FlaggedSpan]] = {}
    for span in flagged_spans:
        spans_by_field.setdefault(span.field, []).append(span)

    sanitized_snapshot: dict[str, str] = {}
    results: list[SanitizationResult] = []
    all_failed_spans: list[dict] = []

    # 模型若返回了快照中不存在的字段，必须显式记为失败，避免“已拦截但未实际处置”。
    for field, spans in spans_by_field.items():
        if field in original_snapshot:
            continue
        for span in spans:
            all_failed_spans.append({
                "field": field,
                "text": span.text,
                "start": span.start,
                "end": span.end,
                "reason": "敏感片段字段不在审核快照中",
            })

    for field, text in original_snapshot.items():
        field_spans = spans_by_field.get(field, [])
        if not field_spans:
            sanitized_snapshot[field] = text
            continue

        result = _apply_spans_to_field(field, text, field_spans)
        sanitized_snapshot[field] = result["sanitized"]
        results.append(result)
        all_failed_spans.extend(result["failed_spans"])

    return sanitized_snapshot, results, all_failed_spans
