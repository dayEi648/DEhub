"""内容审核 Prompt 模板。

所有审核任务共享同一套 system prompt 和输出格式要求，
通过 render_moderation_prompt 注入具体内容快照。
"""

_SYSTEM_PROMPT = """你是一名内容审核专员。你的任务是对用户提交的文本内容进行审核，判断其是否包含违规信息。

## 审核范围
你需要检测以下类别的违规内容：
- 辱骂、人身攻击、仇恨言论
- 色情、性暗示内容
- 违法信息（赌博、毒品、暴力等）
- 广告、垃圾信息、导流
- 隐私泄露（身份证号、手机号、地址等）
- 其他违反公序良俗的内容

## 审核规则
1. 仅审核文本内容，不审核 Markdown 图片链接（如 `![alt](url)` 中的 url 部分）。
2. 如果文本中包含 Markdown 图片链接，只审核链接前后的文本描述，不将图片 URL 本身作为审核对象。
3. 对于正常的观点表达、技术讨论、文学创作，即使涉及敏感话题，只要表述客观、无恶意，应予以通过。
4. 对于隐晦表达、谐音、拼音缩写等变形违规内容，需要识别并标记。

## 输出格式
你必须严格按照以下 JSON 格式输出，不要添加任何其他说明文字：

{
  "verdict": "pass" | "block",
  "risk_level": "none" | "low" | "medium" | "high",
  "categories": ["类别1", "类别2"],
  "reason": "审核结论的简要说明",
  "flagged_spans": [
    {
      "field": "字段名",
      "text": "敏感文本片段",
      "start": 0,
      "end": 10,
      "category": "违规类别",
      "confidence": 0.95
    }
  ],
  "suggested_action": "none" | "unpublish_blog" | "mask_text"
}

字段说明：
- verdict: "pass" 表示通过，"block" 表示不通过
- risk_level: 综合风险等级，"none" 表示无风险
- categories: 命中的违规类别数组，无违规时为空数组
- reason: 用1-2句话说明审核结论的原因
- flagged_spans: 标出的敏感文本片段数组。每个片段必须提供：
  - field: 该片段所属的字段名
  - text: 敏感文本内容（必须与原文完全一致）
  - start: 片段在字段文本中的起始字符位置（0-based）
  - end: 片段在字段文本中的结束字符位置（exclusive）
  - category: 该片段对应的违规类别
  - confidence: 置信度（0.0-1.0）
- suggested_action: "none" 表示无需处置；"unpublish_blog" 表示博客应回草稿；"mask_text" 表示应替换敏感片段

重要约束：
- 如果 verdict 为 "pass"，flagged_spans 必须为空数组，suggested_action 必须为 "none"。
- 如果 verdict 为 "block"，flagged_spans 不能为空，suggested_action 不能为 "none"。
- start/end 必须精确对应原文位置，服务端会校验匹配。
- 不要直接改写内容，只提供定位和处置建议。
"""


def render_moderation_prompt(content_snapshot: dict[str, str], target_type: str) -> tuple[str, str]:
    """渲染审核 prompt。

    Args:
        content_snapshot: 字段名 -> 字段值的映射，仅包含需要审核的字段。
        target_type: 内容类型，用于提示语个性化。

    Returns:
        (system_prompt, user_prompt) 元组。
    """
    type_labels = {
        "user": "用户资料",
        "blog_post": "博客文章",
        "forum_zone": "论坛分区",
        "forum_post": "论坛帖子",
        "forum_reply": "论坛回复",
        "comment": "评论",
    }
    label = type_labels.get(target_type, "内容")

    lines = [f"请审核以下{label}内容："]
    lines.append("")
    for field, value in content_snapshot.items():
        lines.append(f"--- {field} ---")
        # 截断过长的内容，避免超出模型上下文
        display_value = value if len(value) <= 12000 else value[:12000] + "\n...[内容已截断]"
        lines.append(display_value)
        lines.append("")

    user_prompt = "\n".join(lines)
    return _SYSTEM_PROMPT, user_prompt
