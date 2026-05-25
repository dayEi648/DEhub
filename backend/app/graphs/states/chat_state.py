from langchain.agents.middleware.types import AgentState


class ChatState(AgentState):
    """LangGraph 对话状态。

    动态组装 system prompt 所需的运行时字段，随 checkpoint 流转。
    这些字段不直接暴露给前端，仅服务于 prompt 组装中间件。
    """

    user_id: int | None = None
    conversation_id: int | None = None
    profile_text: str | None = None
    prompt_scene: str | None = None
    current_goal: str | None = None
