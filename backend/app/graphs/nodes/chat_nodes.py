import threading

from app.infrastructure.llm_client import get_llm_client
from app.graphs.nodes.toolnodes import search_blog, search_web
from app.graphs.states.chat_state import ChatState


_llm_with_tools = None
_llm_lock = threading.Lock()


def _get_llm_with_tools():
    """获取已绑定 tools 的 LLM 实例（全局单例缓存，线程安全）。"""
    global _llm_with_tools
    if _llm_with_tools is not None:
        return _llm_with_tools
    with _llm_lock:
        if _llm_with_tools is not None:
            return _llm_with_tools
        _llm_with_tools = get_llm_client().bind_tools([search_blog, search_web])
        return _llm_with_tools


def agent_node(state: ChatState) -> dict:
    """
    Agent 节点（带 Tool-Calling 的对话节点）。

    直接从 state.messages 获取完整消息列表（已包含 SystemMessage、
    对话历史和 ToolMessage），调用绑定了 tools 的 LLM。

    Args:
        state: 对话状态

    Returns:
        dict: {"messages": [AIMessage]}（可能包含 tool_calls）
    """
    messages = state.get("messages")
    if not messages:
        return {"messages": []}

    llm = _get_llm_with_tools()
    response = llm.invoke(messages)
    return {"messages": [response]}
