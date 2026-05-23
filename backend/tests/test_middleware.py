"""ConcurrencyMiddleware 单元测试。"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import ToolMessage

from app.graphs.middleware import ConcurrencyMiddleware


class TestConcurrencyMiddleware:
    """测试 ConcurrencyMiddleware 的并发控制策略。"""

    @pytest.fixture
    def middleware(self):
        return ConcurrencyMiddleware()

    @staticmethod
    def _make_request(tool_name: str, tool_call_id: str = "call_1") -> MagicMock:
        """构造模拟的 ToolCallRequest。"""
        request = MagicMock()
        request.tool_call = {"name": tool_name, "args": {}, "id": tool_call_id}
        return request

    # ------------------------------------------------------------------
    # 异步测试
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_safe_tool_executes_in_parallel(self, middleware):
        """concurrency_safe=True 的工具调用应并行执行。"""
        mock_meta = MagicMock()
        mock_meta.concurrency_safe = True

        with patch("app.graphs.middleware.registry.get", return_value=mock_meta):
            call_order: list[tuple[str, str]] = []
            delay = 0.03

            async def handler(req):
                call_order.append(("start", req.tool_call["id"]))
                await asyncio.sleep(delay)
                call_order.append(("end", req.tool_call["id"]))
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req1 = self._make_request("safe_tool", "call_1")
            req2 = self._make_request("safe_tool", "call_2")

            loop = asyncio.get_event_loop()
            start = loop.time()
            results = await asyncio.gather(
                middleware.awrap_tool_call(req1, handler),
                middleware.awrap_tool_call(req2, handler),
            )
            elapsed = loop.time() - start

            # 并行执行：两个调用几乎同时开始，总耗时 ≈ delay（允许一定误差）
            assert elapsed < delay * 2.5
            assert len([e for e in call_order if e[0] == "start"]) == 2
            assert len([e for e in call_order if e[0] == "end"]) == 2
            assert all(isinstance(r, ToolMessage) for r in results)

    @pytest.mark.asyncio
    async def test_unsafe_tool_executes_serially(self, middleware):
        """concurrency_safe=False 的工具调用应串行执行。"""
        mock_meta = MagicMock()
        mock_meta.concurrency_safe = False

        with patch("app.graphs.middleware.registry.get", return_value=mock_meta):
            call_order: list[tuple[str, str]] = []
            delay = 0.03

            async def handler(req):
                call_order.append(("start", req.tool_call["id"]))
                await asyncio.sleep(delay)
                call_order.append(("end", req.tool_call["id"]))
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req1 = self._make_request("unsafe_tool", "call_1")
            req2 = self._make_request("unsafe_tool", "call_2")

            loop = asyncio.get_event_loop()
            start = loop.time()
            results = await asyncio.gather(
                middleware.awrap_tool_call(req1, handler),
                middleware.awrap_tool_call(req2, handler),
            )
            elapsed = loop.time() - start

            # 串行执行：第二个调用等第一个完成后才开始，总耗时 ≈ delay * 2
            assert elapsed >= delay * 1.5
            assert call_order[0] == ("start", "call_1")
            assert call_order[1] == ("end", "call_1")
            assert call_order[2] == ("start", "call_2")
            assert call_order[3] == ("end", "call_2")
            assert all(isinstance(r, ToolMessage) for r in results)

    @pytest.mark.asyncio
    async def test_mixed_safe_and_unsafe_parallel(self, middleware):
        """不同名的安全工具和不安全工具之间无竞争，应并行执行。"""
        safe_meta = MagicMock()
        safe_meta.concurrency_safe = True
        unsafe_meta = MagicMock()
        unsafe_meta.concurrency_safe = False

        def mock_get(name: str):
            return safe_meta if name == "safe_tool" else unsafe_meta

        with patch("app.graphs.middleware.registry.get", side_effect=mock_get):
            delay = 0.03

            async def handler(req):
                await asyncio.sleep(delay)
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req_safe = self._make_request("safe_tool", "call_safe")
            req_unsafe = self._make_request("unsafe_tool", "call_unsafe")

            loop = asyncio.get_event_loop()
            start = loop.time()
            results = await asyncio.gather(
                middleware.awrap_tool_call(req_safe, handler),
                middleware.awrap_tool_call(req_unsafe, handler),
            )
            elapsed = loop.time() - start

            # 不同工具名的锁相互独立，应并行（放宽阈值避免调度误差）
            assert elapsed < delay * 2.5
            assert all(isinstance(r, ToolMessage) for r in results)

    @pytest.mark.asyncio
    async def test_unregistered_tool_treated_as_safe(self, middleware):
        """未注册工具默认视为安全（不加锁）。"""
        with patch("app.graphs.middleware.registry.get", return_value=None):
            delay = 0.03
            running = 0
            max_running = 0

            async def handler(req):
                nonlocal running, max_running
                running += 1
                max_running = max(max_running, running)
                await asyncio.sleep(delay)
                running -= 1
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req1 = self._make_request("unknown_tool", "call_1")
            req2 = self._make_request("unknown_tool", "call_2")

            results = await asyncio.gather(
                middleware.awrap_tool_call(req1, handler),
                middleware.awrap_tool_call(req2, handler),
            )

            assert max_running >= 2
            assert all(isinstance(r, ToolMessage) for r in results)

    # ------------------------------------------------------------------
    # 同步测试
    # ------------------------------------------------------------------

    def test_sync_safe_tool(self, middleware):
        """同步上下文中安全工具直接执行。"""
        mock_meta = MagicMock()
        mock_meta.concurrency_safe = True

        with patch("app.graphs.middleware.registry.get", return_value=mock_meta):
            def handler(req):
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req = self._make_request("safe_tool", "call_1")
            result = middleware.wrap_tool_call(req, handler)

            assert isinstance(result, ToolMessage)
            assert result.content == "ok"

    def test_sync_unsafe_tool(self, middleware):
        """同步上下文中不安全工具直接执行（同步无 asyncio.Lock，默认顺序）。"""
        mock_meta = MagicMock()
        mock_meta.concurrency_safe = False

        with patch("app.graphs.middleware.registry.get", return_value=mock_meta):
            def handler(req):
                return ToolMessage(content="ok", tool_call_id=req.tool_call["id"])

            req = self._make_request("unsafe_tool", "call_1")
            result = middleware.wrap_tool_call(req, handler)

            assert isinstance(result, ToolMessage)
            assert result.content == "ok"
