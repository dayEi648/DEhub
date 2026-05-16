import threading

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.graphs.nodes.chat_nodes import agent_node, retrieve_memory_node
from app.graphs.nodes.toolnodes import search_blog, search_web
from app.graphs.states.chat_state import ChatState
from app.infrastructure.checkpoint_client import get_checkpointer

_compiled_graph = None
_compile_lock = threading.Lock()


def get_chat_graph():
    """获取已编译的对话图实例（全局单例，首次调用时延迟编译，线程安全）。"""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    with _compile_lock:
        if _compiled_graph is not None:
            return _compiled_graph

        builder = StateGraph(ChatState)

        # 注册节点
        builder.add_node("retrieve_memory", retrieve_memory_node)
        builder.add_node("agent", agent_node)
        builder.add_node("tools", ToolNode([search_blog, search_web]))

        # 注册边：先检索记忆，再进入 agent
        builder.add_edge(START, "retrieve_memory")
        builder.add_edge("retrieve_memory", "agent")

        # 条件边：agent 返回 tool_calls 时进入 tools，否则结束
        builder.add_conditional_edges("agent", tools_condition)

        # tool 执行完成后，结果回写 messages，再次进入 agent 生成最终回复
        builder.add_edge("tools", "agent")

        # 编译 + 挂载 Redis checkpointer
        checkpointer = get_checkpointer()
        _compiled_graph = builder.compile(checkpointer=checkpointer)
        return _compiled_graph
