from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """LangGraph 对话状态。

    动态组装 system prompt 所需的运行时字段，随 checkpoint 流转。
    这些字段不直接暴露给前端，仅服务于 prompt 组装节点。
    """

    user_id: int | None = None
    conversation_id: int | None = None
    profile_text: str | None = None
    prompt_scene: str | None = None
    current_goal: str | None = None
    permission_level: int | None = None

    # 上一轮 LLM 调用返回的真实 token 统计（来自 DeepSeek API usage）
    last_prompt_tokens: int | None = None
    last_completion_tokens: int | None = None
    last_total_tokens: int | None = None
    last_cache_hit_tokens: int | None = None
    last_cache_miss_tokens: int | None = None
    last_reasoning_tokens: int | None = None
