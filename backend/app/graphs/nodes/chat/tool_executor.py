"""工具执行节点定义。

解析 AIMessage 中的 tool_calls，按并发安全策略调度执行，
替代原 ToolNode + ConcurrencyMiddleware。
"""

import asyncio
import logging

from langchain_core.messages import AIMessage, ToolMessage

from app.graphs.nodes.toolnodes import registry
from app.graphs.states.chat_state import ChatState

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 模块级锁字典：按工具名维护 asyncio.Lock，确保跨请求串行
# ------------------------------------------------------------------
_locks: dict[str, asyncio.Lock] = {}


def _get_lock(tool_name: str) -> asyncio.Lock:
    """获取指定工具的异步锁（按需创建，线程安全）。"""
    if tool_name not in _locks:
        _locks[tool_name] = asyncio.Lock()
    return _locks[tool_name]


async def _execute_single_tool(tool_call: dict) -> ToolMessage:
    """执行单个 tool_call，异常时包装为 ToolMessage 返回。"""
    tool_name = tool_call["name"]
    tool_call_id = tool_call["id"]
    args = tool_call.get("args", {})

    meta = registry.get(tool_name)
    if meta is None:
        return ToolMessage(
            content=f"Error: 未注册工具 '{tool_name}'",
            tool_call_id=tool_call_id,
            name=tool_name,
        )

    tool = meta.tool
    try:
        if asyncio.iscoroutinefunction(tool.ainvoke if hasattr(tool, "ainvoke") else None):
            result = await tool.ainvoke(args)
        else:
            # 部分工具只实现了同步 invoke，在线程池中运行
            result = await asyncio.to_thread(tool.invoke, args)
        return ToolMessage(
            content=str(result) if result is not None else "",
            tool_call_id=tool_call_id,
            name=tool_name,
        )
    except Exception as exc:
        logger.exception("工具执行失败: tool=%s", tool_name)
        return ToolMessage(
            content=f"Error: {exc}",
            tool_call_id=tool_call_id,
            name=tool_name,
        )


async def tool_executor_node(state: ChatState) -> dict:
    """工具执行节点：按并发策略调度 tool_calls，返回 ToolMessages 列表。"""
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return {"messages": []}

    tool_calls = last_message.tool_calls
    if not tool_calls:
        return {"messages": []}

    # 按并发安全性分组
    safe_calls: list[dict] = []
    unsafe_calls: list[dict] = []
    for tc in tool_calls:
        tool_name = tc["name"]
        meta = registry.get(tool_name)
        if meta is not None and not meta.concurrency_safe:
            unsafe_calls.append(tc)
        else:
            safe_calls.append(tc)

    tool_messages: list[ToolMessage] = []

    # 并行执行安全工具
    if safe_calls:
        safe_tasks = [_execute_single_tool(tc) for tc in safe_calls]
        safe_results = await asyncio.gather(*safe_tasks)
        tool_messages.extend(safe_results)

    # 串行执行非安全工具（按工具名加锁）
    for tc in unsafe_calls:
        tool_name = tc["name"]
        async with _get_lock(tool_name):
            result = await _execute_single_tool(tc)
            tool_messages.append(result)

    return {"messages": tool_messages}
