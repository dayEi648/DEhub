import threading

from langchain.agents import create_agent

from app.graphs.nodes.toolnodes import search_blog, search_web
from app.graphs.states.chat_state import ChatState
from app.infrastructure.checkpoint_client import get_checkpointer
from app.infrastructure.llm_client import get_llm_client

_compiled_graph = None
_compile_lock = threading.Lock()


def get_chat_graph():
    """获取已编译的对话 Agent 实例（全局单例，首次调用时延迟编译，线程安全）。"""
    global _compiled_graph
    if _compiled_graph is not None:
        return _compiled_graph

    with _compile_lock:
        if _compiled_graph is not None:
            return _compiled_graph

        _compiled_graph = create_agent(
            model=get_llm_client(),
            tools=[search_blog, search_web],
            state_schema=ChatState,
            checkpointer=get_checkpointer(),
            name="chat_agent",
        )
        return _compiled_graph
