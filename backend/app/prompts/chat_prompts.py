from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage



# ===================================================================
# Prompts
# ===================================================================
CHAT_DEFAULT_SYSTEM_PROMPT = (
    "你是 DE Hub 网站的 AI 助手，请用中文回答用户的问题。"
    "你性格友好、礼貌，你的说话风格是直接明了，避免非必要的重复对话内容。"
    "DE hub 是开发者 DaiEe 的个人博客网站，"
    "用于展示个人的作品、学习笔记、开发经验等；"
    "该网站有论坛版块，支持其他用户在论坛中交流。\n\n"
    "你拥有以下 2 个 Tool，可按需调用：\n"
    "1. search_blog：检索 DE Hub 博客文章。"
    "当用户与你的交流提及 DE Hub 的博客文章，"
    "或者用户表达出了对博客文章的兴趣时，请使用该工具，需要时可以提供跳转链接。\n"
    "2. search_web：联网搜索获取实时信息。"
    "当用户询问时事新闻、最新技术动态、股价天气等时效性内容，"
    "或明确要求'搜索一下''联网搜索'时，请使用该工具。"
)

CHAT_MEMORY_BLOCK_PROMPT = (
    "--- 用户历史记忆 ---\n"
    "以下是根据当前问题检索到的用户相关历史记忆，"
    '请自然地结合这些记忆进行个性化回复，不要提及"检索记忆"这一过程：\n\n'
    "{memories}\n"
    "---\n"
)

CONVERSATION_SUMMARY_PROMPT = (
    "请根据以下对话记录，提取并总结关于用户的画像信息。"
    "重点关注用户侧信息，少量参考 AI 助手的话语信息。\n\n"
    "关注以下方面：\n"
    "- 用户的性格特点、说话风格\n"
    "- 用户的兴趣、偏好、习惯\n"
    "- 用户做过什么、计划做什么\n"
    "- 用户的技能水平、知识背景或职业\n\n"
    "用第三人称简洁描述，控制在 100 字以内。"
    "如果对话太短不足以提取有效画像，请返回空字符串。"
)

CONVERSATION_TITLE_PROMPT = (
    "请根据以下用户输入，生成一个简短的对话标题（15字以内）。"
    "标题应概括用户的核心需求或话题，不要包含寒暄。"
    "只输出标题文字，不要加引号，不要添加任何解释。"
)



# ===================================================================
# Functions
# ===================================================================

def _format_memories(memories: list[str]) -> str:
    """将记忆列表格式化为编号文本。"""
    return "\n".join(f"{i + 1}. {m}" for i, m in enumerate(memories))


def get_chat_system_prompt(memories: list[str] | None = None) -> ChatPromptTemplate:
    """
    对话 System Prompt。

    当传入记忆列表时，在 system prompt 中追加用户画像记忆区块；
    无记忆时返回默认版本。

    MessagesPlaceholder 让 LangGraph 自动把历史消息列表注入到 'messages' 槽位。
    """
    if memories:
        memory_block = CHAT_MEMORY_BLOCK_PROMPT.format(
            memories=_format_memories(memories)
        )
        full_prompt = f"{CHAT_DEFAULT_SYSTEM_PROMPT}\n\n{memory_block}"
    else:
        full_prompt = CHAT_DEFAULT_SYSTEM_PROMPT

    return ChatPromptTemplate.from_messages([
        SystemMessage(content=full_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
