"""Agent 输出质量评估 Prompt 模板。

使用 LLM-as-Judge 对 Agent Trace 进行多维度评分。
要求模型输出结构化 JSON: {"score": 0.85, "reason": "..."}
"""

from __future__ import annotations


# -------------------------------------------------------------------
# Relevance 评估：AI 回复是否与用户输入相关
# -------------------------------------------------------------------
RELEVANCE_EVAL_PROMPT = (
    "你是一名极其严格的质量评估专家。请评估以下 AI 助手回复与用户输入的相关性。\n\n"
    "评估步骤（必须先执行）：\n"
    "1. 提炼用户输入的核心意图和关键需求点\n"
    "2. 检查 AI 回复是否精准命中了这些需求点\n"
    "3. 列出 1~3 条具体的不足（如：遗漏了什么、多了什么无关内容、理解偏差等）\n"
    "4. 根据不足扣分后给出最终分数\n\n"
    "评分标准（0.00 ~ 1.00），严格执行：\n"
    "- 0.90~1.00：回复精准命中用户所有核心需求，零冗余，零偏差（极少出现）\n"
    "- 0.70~0.89：回复基本相关，但包含少量冗余信息，或某个次要需求未完全覆盖\n"
    "- 0.50~0.69：回复部分相关，遗漏了用户的一个核心需求点，或存在明显理解偏差\n"
    "- 0.30~0.49：回复与用户问题关联较弱，只触及了边缘信息\n"
    "- 0.10~0.29：回复基本无关，答非所问或大量冗余\n"
    "- 0.00：完全无关\n\n"
    "重要校准：绝大多数普通回复应该落在 0.55~0.80 之间。只有真正无可挑剔的回复才能给 0.90+。\n\n"
    "用户输入：\n"
    "{input_message}\n\n"
    "AI 回复：\n"
    "{output_message}\n\n"
    "工具调用情况：{tool_calls_summary}\n\n"
    "请输出 JSON（不要包含任何其他文字，reason 用中文）：\n"
    '{{"score": <0.00~1.00>, "reason": "<先列出不足，再给出分数理由>"}}'
)

# -------------------------------------------------------------------
# Helpfulness 评估：AI 回复是否有用
# -------------------------------------------------------------------
HELPFULNESS_EVAL_PROMPT = (
    "你是一名极其严格的质量评估专家。请评估以下 AI 助手回复的有用性。\n\n"
    "评估步骤（必须先执行）：\n"
    "1. 判断用户需要的是事实、步骤、代码、建议还是情感支持\n"
    "2. 检查 AI 回复是否提供了可操作、可落地的信息，还是仅停留在泛泛而谈\n"
    "3. 列出 1~3 条具体的不足（如：缺少关键步骤、信息不够具体、没有示例等）\n"
    "4. 根据不足扣分后给出最终分数\n\n"
    "评分标准（0.00 ~ 1.00），严格执行：\n"
    "- 0.90~1.00：回复极其有用，不仅完整解决问题，还提供了额外有价值的延伸信息（极少出现）\n"
    "- 0.70~0.89：回复有用，基本解决了问题，但可能缺少具体示例或某一步骤不够详细\n"
    "- 0.50~0.69：回复有一定帮助，但过于概括，用户看完可能还需要进一步追问\n"
    "- 0.30~0.49：回复帮助很小，只提供了背景知识或定义，没有针对用户场景给出方案\n"
    "- 0.10~0.29：回复几乎没有帮助，全是套话或免责声明\n"
    "- 0.00：完全无用，甚至包含有害或错误信息\n\n"
    "硬性扣分规则：\n"
    "- 如果用户要求具体步骤/代码/示例，但回复中没有提供 → 最高 0.60\n"
    "- 如果回复主要是概括性描述，没有 actionable 内容 → 最高 0.65\n"
    "- 如果回复中包含'你可以尝试搜索更多信息'这类推卸责任的表达 → 扣 0.20\n\n"
    "重要校准：绝大多数普通回复应该落在 0.55~0.80 之间。只有真正无可挑剔的回复才能给 0.90+。\n\n"
    "用户输入：\n"
    "{input_message}\n\n"
    "AI 回复：\n"
    "{output_message}\n\n"
    "工具调用情况：{tool_calls_summary}\n\n"
    "请输出 JSON（不要包含任何其他文字，reason 用中文）：\n"
    '{{"score": <0.00~1.00>, "reason": "<先列出不足，再给出分数理由>"}}'
)

# -------------------------------------------------------------------
# Coherence 评估：回复是否连贯、结构清晰
# -------------------------------------------------------------------
COHERENCE_EVAL_PROMPT = (
    "你是一名极其严格的质量评估专家。请评估以下 AI 助手回复的连贯性和结构清晰度。\n\n"
    "评估步骤（必须先执行）：\n"
    "1. 检查回复的逻辑链条是否完整（论点→论据→结论）\n"
    "2. 检查段落之间是否有突兀跳跃或断裂\n"
    "3. 检查是否存在前后矛盾、重复啰嗦、或突然切换话题\n"
    "4. 列出 1~3 条具体的结构问题\n"
    "5. 根据问题扣分后给出最终分数\n\n"
    "评分标准（0.00 ~ 1.00），严格执行：\n"
    "- 0.90~1.00：结构完美，逻辑严密，无任何可挑剔之处（极少出现）\n"
    "- 0.70~0.89：基本连贯，偶有轻微表达问题，但不影响理解\n"
    "- 0.50~0.69：存在 1~2 处逻辑跳跃或表达不清，需要读者自行脑补\n"
    "- 0.30~0.49：存在多处逻辑断裂或前后矛盾，理解困难\n"
    "- 0.10~0.29：非常混乱，段落之间毫无关联\n"
    "- 0.00：完全无法阅读\n\n"
    "硬性扣分规则：\n"
    "- 每出现一处明显的逻辑断裂或话题跳跃 → 扣 0.10\n"
    "- 出现前后矛盾 → 最高 0.50\n"
    "- 存在大量重复啰嗦内容 → 扣 0.10~0.20\n\n"
    "重要校准：绝大多数普通回复应该落在 0.60~0.85 之间。只有真正无可挑剔的回复才能给 0.90+。\n\n"
    "AI 回复：\n"
    "{output_message}\n\n"
    "请输出 JSON（不要包含任何其他文字，reason 用中文）：\n"
    '{{"score": <0.00~1.00>, "reason": "<先列出不足，再给出分数理由>"}}'
)


def _build_tool_calls_summary(tool_calls_count: int, spans: list[dict] | None) -> str:
    """构建工具调用摘要文本。"""
    if tool_calls_count == 0:
        return "未调用任何工具"

    if not spans:
        return f"调用了 {tool_calls_count} 个工具"

    tool_names = []
    for span in spans:
        if span.get("span_type") == "tool":
            name = span.get("span_name", "unknown")
            if name not in tool_names:
                tool_names.append(name)

    if tool_names:
        return f"调用了 {tool_calls_count} 个工具: {', '.join(tool_names)}"
    return f"调用了 {tool_calls_count} 个工具"


def render_relevance_eval_prompt(
    input_message: str | None,
    output_message: str | None,
    tool_calls_count: int = 0,
    spans: list[dict] | None = None,
) -> str:
    """渲染相关性评估 prompt。"""
    return RELEVANCE_EVAL_PROMPT.format(
        input_message=input_message or "（无输入）",
        output_message=output_message or "（无输出）",
        tool_calls_summary=_build_tool_calls_summary(tool_calls_count, spans),
    )


def render_helpfulness_eval_prompt(
    input_message: str | None,
    output_message: str | None,
    tool_calls_count: int = 0,
    spans: list[dict] | None = None,
) -> str:
    """渲染有用性评估 prompt。"""
    return HELPFULNESS_EVAL_PROMPT.format(
        input_message=input_message or "（无输入）",
        output_message=output_message or "（无输出）",
        tool_calls_summary=_build_tool_calls_summary(tool_calls_count, spans),
    )


def render_coherence_eval_prompt(
    output_message: str | None,
) -> str:
    """渲染连贯性评估 prompt。"""
    return COHERENCE_EVAL_PROMPT.format(
        output_message=output_message or "（无输出）",
    )
