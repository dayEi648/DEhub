"""
LangGraph State 定义。
"""
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Agent 状态定义，贯穿 Graph 执行全流程。"""

    user_id: int
    session_id: str
    jwt_token: str
    messages: Annotated[list[BaseMessage], add_messages]
    user_input: str
    intent: str
    emotion_tags: list[str]
    interest_tags: list[str]
    retrieved_docs: list[dict]
    tool_results: list[dict]
    response: str
    streaming: bool
