from app.infrastructure.llm_client import get_llm_client
from app.prompts.chat_prompts import get_chat_default_system_prompt
from app.graphs.states.chat_state import ChatState

_chat_chain = None


def _get_chat_chain():
    """延迟初始化对话链，避免在模块导入时调用未初始化的 LLM 客户端。"""
    global _chat_chain
    if _chat_chain is None:
        _llm_main = get_llm_client()
        _chat_system_prompt = get_chat_default_system_prompt()
        _chat_chain = _chat_system_prompt | _llm_main
    return _chat_chain


def chat_node(state: ChatState) -> dict:
    """
    对话节点
    Args:
        state: 对话状态
    Returns:
        dict: 对话结果
    """
    # state["messages"] 已经包含完整历史（由 checkpointer 自动恢复）
    response = _get_chat_chain().invoke({"messages": state["messages"]})
    return {"messages": [response]}

