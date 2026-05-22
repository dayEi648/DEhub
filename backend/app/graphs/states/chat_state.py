from langchain.agents.middleware.types import AgentState


class ChatState(AgentState):
    """LangGraph 对话状态。"""

    user_id: int | None = None
    conversation_id: int | None = None
