from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage



# ===================================================================
# Prompts
# ===================================================================
CHAT_DEFAULT_SYSTEM_PROMPT = (
    "你是 DE Hub 网站的 AI 助手，性格热情且友好；请用中文回答用户的问题；你的说话风格是直接明了，避免非必要的重复对话内容；如果你与用户的交流涉及 DE hub 网站博客里的文章，并且用户表现出了对博客文章的兴趣或者他明确要求你给出文章的链接，那么你要在回答中提供该文章的跳转链接。"
)

CONVERSATION_SUMMARY_PROMPT = (
    "请根据以下对话记录，提取并总结关于用户的画像信息。"
    "只关注用户侧信息，完全忽略 AI 助手的回复内容。"
    "\n\n"
    "关注以下方面：\n"
    "- 用户的性格特点、说话风格\n"
    "- 用户的兴趣、偏好、习惯\n"
    "- 用户做过什么、计划做什么\n"
    "- 用户的技能水平、知识背景或职业\n"
    "\n"
    "用第三人称简洁描述，控制在 200 字以内。"
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

def get_chat_default_system_prompt() -> ChatPromptTemplate:
    """
    对话 System Prompt
    MessagesPlaceholder 让 LangGraph 自动把历史消息列表注入到 'messages' 槽位。
    """
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=CHAT_DEFAULT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages"),
    ])
