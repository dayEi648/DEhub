"""Agent 中间件：工具执行策略控制。

使用 LangChain 官方 `AgentMiddleware` 机制，在不触碰 `ToolNode` 内部的前提下，
通过 `awrap_tool_call` / `wrap_tool_call` 钩子实现并发调度策略。
"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain.agents.middleware import AgentMiddleware
from langgraph.prebuilt.tool_node import ToolCallRequest

from app.graphs.nodes.toolnodes import registry


class ConcurrencyMiddleware(AgentMiddleware):
    """并发控制中间件。

    根据 `ToolMetadata.concurrency_safe` 决定工具调用策略：
    - `concurrency_safe=True`（默认）：直接执行，与默认行为一致
    - `concurrency_safe=False`：获取该工具的 `asyncio.Lock`，确保串行执行

    锁粒度：按工具名。未来可按 `(tool_name, resource_id)` 细化。
    """

    def __init__(self) -> None:
        super().__init__()
        # 按需创建工具级锁，避免未注册工具占用内存
        self._locks: dict[str, asyncio.Lock] = {}

    @property
    def name(self) -> str:
        return "concurrency_control"

    def _get_lock(self, tool_name: str) -> asyncio.Lock:
        """获取指定工具的异步锁（按需创建，线程安全）。"""
        if tool_name not in self._locks:
            self._locks[tool_name] = asyncio.Lock()
        return self._locks[tool_name]

    def _should_serialize(self, tool_name: str) -> bool:
        """判断指定工具是否需要串行执行。"""
        meta = registry.get(tool_name)
        if meta is None:
            # 未注册工具走默认策略（视为安全）
            return False
        return not meta.concurrency_safe

    def wrap_tool_call(self, request: ToolCallRequest, handler) -> Any:
        """同步拦截：不安全工具直接串行执行（无并发场景）。"""
        tool_name = request.tool_call["name"]
        if self._should_serialize(tool_name):
            # 同步上下文无 asyncio.Lock，直接顺序执行即可
            return handler(request)
        return handler(request)

    async def awrap_tool_call(self, request: ToolCallRequest, handler) -> Any:
        """异步拦截：不安全工具加锁排队，实现串行效果。"""
        tool_name = request.tool_call["name"]
        if self._should_serialize(tool_name):
            async with self._get_lock(tool_name):
                return await handler(request)
        return await handler(request)
