from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """
    LangGraph 对话状态
    """
    user_id: int = 0
    conversation_id: int | None = None
