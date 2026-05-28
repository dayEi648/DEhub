"""
LangGraph 构建与编译。
定义节点、条件边，组装完整的状态图。
"""
from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from app.graph.nodes.recommend import recommend_node
from app.graph.nodes.retrieve import retrieve_node
from app.graph.nodes.tool_call import tool_call_node
from app.graph.nodes.understand import understand_node
from app.graph.state import AgentState


def _entry_node(state: AgentState) -> dict:
    """入口节点：将 user_input 转为 HumanMessage 加入 messages。"""
    return {"messages": [HumanMessage(content=state["user_input"])]}


def _route_after_understand(state: AgentState) -> str:
    """条件路由：根据意图分发到不同 action 节点或直接结束。"""
    intent = state.get("intent", "chat")
    if intent in ("emotion_recommend", "interest_recommend", "profile_recommend"):
        return "recommend"
    elif intent == "knowledge_query":
        return "retrieve"
    elif intent in ("web_search", "music_action"):
        return "tool_call"
    else:
        return "end"


def build_graph():
    """构建并编译 StateGraph。"""
    workflow = StateGraph(AgentState)

    # 注册节点
    workflow.add_node("entry", _entry_node)
    workflow.add_node("understand", understand_node)
    workflow.add_node("recommend", recommend_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("tool_call", tool_call_node)

    # 入口 → 意图理解
    workflow.set_entry_point("entry")
    workflow.add_edge("entry", "understand")

    # 意图理解 → 条件路由
    workflow.add_conditional_edges(
        "understand",
        _route_after_understand,
        {
            "recommend": "recommend",
            "retrieve": "retrieve",
            "tool_call": "tool_call",
            "end": END,
        },
    )

    # action 节点 → 结束
    workflow.add_edge("recommend", END)
    workflow.add_edge("retrieve", END)
    workflow.add_edge("tool_call", END)

    return workflow.compile()


# 全局编译后的图实例
graph = build_graph()
