import threading

from langchain.agents import create_agent

from app.graphs.middleware import ConcurrencyMiddleware
from app.graphs.nodes.toolnodes import registry
from app.graphs.states.chat_state import ChatState
from app.infrastructure.checkpoint_client import get_checkpointer
from app.infrastructure.llm_client import get_llm_client

_graph_cache: dict[tuple[int, str], object] = {}
_compile_lock = threading.Lock()


def get_chat_graph(permission_level: int = 0):
    """获取已编译的对话 Agent 实例（按权限等级缓存，线程安全）。

    Args:
        permission_level: 当前用户权限等级（0=USER, 1=ADMIN, 2=SUPER_ADMIN）。
                          用于动态过滤可见工具。

    Returns:
        已编译的 LangGraph CompiledStateGraph 实例。
    """
    # 从注册中心解析当前用户可见的工具列表
    active_tools = registry.resolve(permission_level)
    tools_key = ",".join(sorted(t.name for t in active_tools))
    cache_key = (permission_level, tools_key)

    # 快速路径：已缓存直接返回
    cached = _graph_cache.get(cache_key)
    if cached is not None:
        return cached

    # 慢速路径：首次编译，加锁保证单例
    with _compile_lock:
        cached = _graph_cache.get(cache_key)
        if cached is not None:
            return cached

        compiled = create_agent(
            model=get_llm_client(),
            tools=active_tools,
            state_schema=ChatState,
            checkpointer=get_checkpointer(),
            name="chat_agent",
            middleware=[ConcurrencyMiddleware()],
        )
        _graph_cache[cache_key] = compiled
        return compiled
