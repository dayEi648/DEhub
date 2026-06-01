"""Agent 条件路由函数。"""

from langchain_core.messages import AIMessage
from langgraph.graph import END

from app.graphs.states.chat_state import ChatState


def route_after_agent(state: ChatState) -> str:
    """根据 agent 节点的输出决定下一跳。

    - 若最后一条 AIMessage 包含 tool_calls，路由到 tool_executor 继续 ReAct 循环
    - 否则结束图执行
    """
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_executor"

    return END
