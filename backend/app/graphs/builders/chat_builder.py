from app.graphs.states.chat_state import ChatState
from app.graphs.nodes.chat_nodes import retrieve_memory_node, chat_node
from langgraph.graph import StateGraph, START, END
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
    builder.add_node("chat", chat_node)

    # 注册边：先检索记忆，再对话
    builder.add_edge(START, "retrieve_memory")
    builder.add_edge("retrieve_memory", "chat")
    builder.add_edge("chat", END)

    # 编译 + 挂载记忆checkpointer
    memory = MemorySaver()
    _compiled_graph = builder.compile(checkpointer=memory)
    return _compiled_graph
