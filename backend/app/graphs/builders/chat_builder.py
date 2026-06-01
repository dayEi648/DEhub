"""Chat Agent 图编译器。

从原 create_agent 黑盒迁移为显式 StateGraph 多节点编排，
保留所有外部调用接口（ainvoke / aget_state / aupdate_state）不变。
"""

from langgraph.graph import END, START, StateGraph

from app.graphs.nodes.chat import agent_node, route_after_agent, tool_executor_node
from app.graphs.states.chat_state import ChatState
from app.infrastructure.checkpoint_client import get_checkpointer

_graph_instance = None


def get_chat_graph():
    """获取已编译的对话 Agent 图实例（全局单例）。

    Returns:
        已编译的 LangGraph CompiledStateGraph 实例。
    """
    global _graph_instance
    if _graph_instance is not None:
        return _graph_instance

    workflow = StateGraph(ChatState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tool_executor", tool_executor_node)

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tool_executor": "tool_executor", END: END},
    )
    workflow.add_edge("tool_executor", "agent")

    _graph_instance = workflow.compile(
        checkpointer=get_checkpointer(),
        name="chat_agent",
    )
    return _graph_instance
