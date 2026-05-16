from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """LangGraph 对话状态。"""
    user_id: int | None = None
    conversation_id: int | None = None
    retrieved_memories: list[str] = []
