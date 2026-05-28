"""
意图理解节点。
调用 LLM 分析用户输入的意图，并提取情绪/兴趣标签。
"""
import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.graph.state import AgentState
from app.graph.tools.tag_pool import tag_pool_service
from app.services.llm_service import llm_service

_UNDERSTAND_SYSTEM = """你是一个专业的用户意图分析助手。
你的任务是分析用户的输入，判断其意图类别，并提取相关标签。
请始终以 JSON 格式返回结果，不要包含任何解释性文字。"""

_UNDERSTAND_TEMPLATE = """请分析以下用户输入，判断意图并提取标签。

可选意图类别：
- chat：普通聊天、问候、闲聊
- emotion_recommend：基于情绪状态推荐音乐（如"心情不好听什么"、"开心时听什么"）
- interest_recommend：基于兴趣/场景推荐音乐（如"运动时听什么"、"摇滚推荐"）
- profile_recommend：基于用户画像/听歌习惯推荐音乐（如"根据我的听歌习惯推荐"、"推荐我喜欢的类型"）
- knowledge_query：查询平台规则、音乐知识、功能说明
- web_search：查询实时信息（天气、新闻、事件等）
- music_action：音乐操作（播放、收藏、加入歌单等）

{tag_pool_section}

当前对话历史（最近10轮）：
{history}

用户输入：{user_input}

请以 JSON 格式返回，不要包含其他内容：
{{
  "intent": "chat|emotion_recommend|interest_recommend|profile_recommend|knowledge_query|web_search|music_action",
  "emotion_tags": [],
  "interest_tags": [],
  "reasoning": "简要判断理由"
}}
"""

_VALID_INTENTS = {
    "chat",
    "emotion_recommend",
    "interest_recommend",
    "profile_recommend",
    "knowledge_query",
    "web_search",
    "music_action",
}


def _extract_json(text: str) -> dict:
    """从文本中提取 JSON 对象，支持 markdown 代码块。"""
    patterns = [
        r"```json\s*(.*?)\s*```",
        r"```\s*(.*?)\s*```",
        r"(\{.*?\})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return {}


async def understand_node(state: AgentState) -> dict:
    """
    意图理解节点。
    分析用户输入，返回 intent、emotion_tags、interest_tags。
    """
    tags = await tag_pool_service.get_tags()

    if tags:
        displayed = tags[:100]
        total = len(tags)
        tag_pool_section = (
            f"合法标签池（共 {total} 个，展示前 {len(displayed)} 个，"
            f"推荐标签必须从中选择）：\n"
            + "\n".join([f"- {t}" for t in displayed])
        )
    else:
        tag_pool_section = "（当前标签池为空）"

    # 构造最近10轮历史
    history_msgs = (
        state["messages"][-10:]
        if len(state["messages"]) > 10
        else state["messages"]
    )
    history_lines = []
    for msg in history_msgs:
        # 过滤 SystemMessage，避免系统提示混入对话历史
        if msg.type == "system":
            continue
        if msg.type == "human":
            role = "用户"
        elif msg.type == "ai":
            role = "AI"
        else:
            role = msg.type
        content = (
            msg.content[:150]
            if isinstance(msg.content, str)
            else str(msg.content)[:150]
        )
        history_lines.append(f"{role}: {content}")
    history_text = "\n".join(history_lines) or "（无历史对话）"

    prompt = _UNDERSTAND_TEMPLATE.format(
        tag_pool_section=tag_pool_section,
        history=history_text,
        user_input=state["user_input"],
    )

    result_text = await llm_service.achat(
        [
            SystemMessage(content=_UNDERSTAND_SYSTEM),
            HumanMessage(content=prompt),
        ]
    )

    # 解析 JSON
    try:
        parsed = json.loads(result_text.strip())
    except json.JSONDecodeError:
        parsed = _extract_json(result_text)

    intent = parsed.get("intent", "chat")
    emotion_tags = parsed.get("emotion_tags", []) or []
    interest_tags = parsed.get("interest_tags", []) or []

    # 过滤非法标签
    if tags:
        valid_tags = set(tags)
        emotion_tags = [t for t in emotion_tags if t in valid_tags]
        interest_tags = [t for t in interest_tags if t in valid_tags]

    # 确保意图合法
    if intent not in _VALID_INTENTS:
        intent = "chat"

    return {
        "intent": intent,
        "emotion_tags": emotion_tags,
        "interest_tags": interest_tags,
    }
