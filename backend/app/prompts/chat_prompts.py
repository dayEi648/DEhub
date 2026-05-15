from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage



# ===================================================================
# Prompts
# ===================================================================
CHAT_DEFAULT_SYSTEM_PROMPT = (
    "你是 DE Hub 网站的 AI 助手，性格热情且友好；请用中文回答用户的问题；你的说话风格是直接明了，避免非必要的重复对话内容；如果你与用户的交流涉及 DE hub 网站博客里的文章，并且用户表现出了对博客文章的兴趣或者他明确要求你给出文章的链接，那么你要在回答中提供该文章的跳转链接。"
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
