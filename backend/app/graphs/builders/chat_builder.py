from app.graphs.states.chat_state import ChatState
from app.graphs.nodes.chat_nodes import retrieve_memory_node, agent_node
from app.tools.blog_search import search_blog
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

_compiled_graph = None


def build_chat_graph():
    """
    构建并编译对话图（全局单例）
    """
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    builder = StateGraph(ChatState)

    # 注册节点
    builder.add_node("retrieve_memory", retrieve_memory_node)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode([search_blog]))

    # 注册边：先检索记忆，再进入 agent
    builder.add_edge(START, "retrieve_memory")
    builder.add_edge("retrieve_memory", "agent")

    # 条件边：agent 返回 tool_calls 时进入 tools，否则结束
    builder.add_conditional_edges("agent", tools_condition)

    # tool 执行完成后，结果回写 messages，再次进入 agent 生成最终回复
    builder.add_edge("tools", "agent")

    # 编译 + 挂载记忆 checkpointer
    memory = MemorySaver()
    _compiled_graph = builder.compile(checkpointer=memory)
    return _compiled_graph
