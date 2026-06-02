"""Agent 节点定义。

内部显式实现 Prompt 组装、动态工具绑定与 LLM 调用，
替代原 PromptAssemblyMiddleware + create_agent 黑盒。
"""

from datetime import datetime

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from app.graphs.nodes.toolnodes import registry
from app.graphs.states.chat_state import ChatState
from app.infrastructure.llm_client import get_llm_client
from app.prompts.chat_prompts import render_chat_system_prompt


# ------------------------------------------------------------------
# 模块级缓存：按 permission_level 缓存 bind_tools 后的模型实例
# ------------------------------------------------------------------
_bound_models: dict[int, BaseTool] = {}


def _get_bound_model(permission_level: int):
    """获取已绑定工具的模型实例（首次绑定后缓存复用）。"""
    if permission_level not in _bound_models:
        active_tools = registry.resolve(permission_level)
        _bound_models[permission_level] = get_llm_client().bind_tools(active_tools)
    return _bound_models[permission_level]


def _filter_system_messages(messages: list) -> list:
    """过滤消息列表中的旧 SystemMessage。"""
    return [m for m in messages if not isinstance(m, SystemMessage)]


def _resolve_scene(state: ChatState) -> str | None:
    """根据状态和历史消息解析当前场景。"""
    from langchain_core.messages import ToolMessage

    scene = state.get("prompt_scene")
    messages = state.get("messages", [])
    if messages and isinstance(messages[-1], ToolMessage):
        return "工具结果返回后继续回答"
    return scene


def _render_system_prompt(state: ChatState) -> str:
    """渲染合并后的 system prompt 内容。"""
    scene = _resolve_scene(state)
    return render_chat_system_prompt(
        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scene=scene,
        profile_text=state.get("profile_text"),
        current_goal=state.get("current_goal"),
        permission_level=state.get("permission_level"),
    )


async def agent_node(state: ChatState, config: RunnableConfig) -> dict:
    """Agent 节点：组装 Prompt → 绑定工具 → 调用 LLM → 返回 AIMessage。

    注意：SystemMessage 仅作为 LLM 调用的临时参数，不写入 state["messages"]，
    以精确复现原 PromptAssemblyMiddleware 的行为。
    """
    # 1. 组装 Prompt
    cleaned_messages = _filter_system_messages(state.get("messages", []))
    system_prompt = _render_system_prompt(state)
    messages_for_llm = [SystemMessage(content=system_prompt), *cleaned_messages]

    # 2. 动态绑定工具
    permission_level = state.get("permission_level") or 0
    model = _get_bound_model(permission_level)

    # 3. 调用 LLM
    response = await model.ainvoke(messages_for_llm, config)

    # 4. 提取 DeepSeek API 返回的真实 token usage
    usage_meta = response.usage_metadata or {}
    resp_meta = response.response_metadata or {}
    token_usage = resp_meta.get("token_usage") or {}
    completion_details = token_usage.get("completion_tokens_details") or {}

    # 5. 返回 AIMessage + token 统计（add_messages reducer 会自动追加 messages）
    return {
        "messages": [response],
        "last_prompt_tokens": usage_meta.get("input_tokens"),
        "last_completion_tokens": usage_meta.get("output_tokens"),
        "last_total_tokens": usage_meta.get("total_tokens"),
        "last_cache_hit_tokens": token_usage.get("prompt_cache_hit_tokens"),
        "last_cache_miss_tokens": token_usage.get("prompt_cache_miss_tokens"),
        "last_reasoning_tokens": completion_details.get("reasoning_tokens"),
    }
