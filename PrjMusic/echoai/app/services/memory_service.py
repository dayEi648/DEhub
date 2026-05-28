"""
记忆管理服务。
负责多轮对话的记忆管理：
- PostgreSQL 持久化（ai_sessions / ai_messages）
- Redis 内存缓存（近期消息加速读取）
- 长期记忆摘要生成
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

from app.config import settings
from app.services.llm_service import llm_service
from app.utils.async_db import db_pools
from app.utils.redis_pool import redis_client


class MemoryService:
    """记忆管理服务：PG 持久化 + Redis 缓存。"""

    REDIS_PREFIX = "ai:memory"
    REDIS_MAX_MESSAGES = 20
    REDIS_TTL = 1800  # 30分钟
    SUMMARY_THRESHOLD = 20  # 消息数超过此值时生成摘要

    # ------------------------------------------------------------------ #
    # 消息存取
    # ------------------------------------------------------------------ #

    async def save_message(
        self,
        session_id: str,
        user_id: int,
        role: str,
        content: str,
        tool_calls: Optional[dict | list] = None,
        tool_call_id: Optional[str] = None,
    ) -> dict:
        """
        保存单条消息到 PG，并同步更新 Redis 缓存。
        返回包含 id 和 create_time 的字典。
        """
        async with db_pools.echomusic.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ai_messages (session_id, user_id, role, content, tool_calls, tool_call_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, create_time
                """,
                session_id,
                user_id,
                role,
                content,
                json.dumps(tool_calls) if tool_calls is not None else None,
                tool_call_id,
            )

        # 同步 Redis：LPUSH + LTRIM + EXPIRE
        redis_key = f"{self.REDIS_PREFIX}:{user_id}:{session_id}"
        msg_data = json.dumps(
            {
                "role": role,
                "content": content,
                "tool_calls": tool_calls,
                "tool_call_id": tool_call_id,
                "create_time": row["create_time"].isoformat(),
            },
            ensure_ascii=False,
            default=str,
        )

        async with redis_client.client.pipeline() as pipe:
            pipe.lpush(redis_key, msg_data)
            pipe.ltrim(redis_key, 0, self.REDIS_MAX_MESSAGES - 1)
            pipe.expire(redis_key, self.REDIS_TTL)
            await pipe.execute()

        return {"id": row["id"], "create_time": row["create_time"]}

    async def load_messages(
        self,
        session_id: str,
        user_id: int,
        limit: int = 50,
    ) -> list[BaseMessage]:
        """
        加载历史消息，优先读 Redis，miss 则查 PG 并回填。
        返回 LangChain BaseMessage 列表（按时间正序）。
        """
        redis_key = f"{self.REDIS_PREFIX}:{user_id}:{session_id}"

        # 1) 尝试 Redis
        cached = await redis_client.client.lrange(redis_key, 0, limit - 1)
        if cached:
            # Redis LPUSH 导致顺序是倒序，需要反转
            cached = list(reversed(cached))
            messages = [
                m for m in (self._deserialize_message(c) for c in cached) if m is not None
            ]
            # 续期 TTL
            await redis_client.client.expire(redis_key, self.REDIS_TTL)
            return messages

        # 2) Miss，获取回填锁防止并发重复回填导致消息乱序/重复
        lock_key = f"{self.REDIS_PREFIX}:lock:{session_id}"
        lock_acquired = await redis_client.client.set(lock_key, "1", nx=True, ex=5)
        if not lock_acquired:
            # 其他进程正在回填，等待后重试读 Redis
            await asyncio.sleep(0.3)
            cached = await redis_client.client.lrange(redis_key, 0, limit - 1)
            if cached:
                cached = list(reversed(cached))
                messages = [
                m for m in (self._deserialize_message(c) for c in cached) if m is not None
            ]
                await redis_client.client.expire(redis_key, self.REDIS_TTL)
                return messages
            # 兜底：继续走 PG 查询

        async with db_pools.echomusic.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, tool_calls, tool_call_id, create_time
                FROM ai_messages
                WHERE session_id = $1
                ORDER BY create_time DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )

        if not rows:
            if lock_acquired:
                await redis_client.client.delete(lock_key)
            return []

        # 3) 回填 Redis（DESC 查询结果是 [最新, ..., 较旧]，需反转后 LPUSH，
        #    使 Redis 列表保持 [最新, ..., 较旧]，与 save_message 一致）
        pipe = redis_client.client.pipeline()
        for row in reversed(rows):
            msg_data = json.dumps(
                {
                    "role": row["role"],
                    "content": row["content"],
                    "tool_calls": row["tool_calls"],
                    "tool_call_id": row["tool_call_id"],
                    "create_time": row["create_time"].isoformat(),
                },
                ensure_ascii=False,
                default=str,
            )
            pipe.lpush(redis_key, msg_data)
        pipe.ltrim(redis_key, 0, self.REDIS_MAX_MESSAGES - 1)
        pipe.expire(redis_key, self.REDIS_TTL)
        await pipe.execute()

        if lock_acquired:
            await redis_client.client.delete(lock_key)

        # rows 是 DESC 顺序 [最新, ..., 较旧]，返回前反转为时间正序
        return [self._deserialize_row(r) for r in reversed(rows)]

    def _deserialize_message(self, data: str) -> BaseMessage | None:
        try:
            d = json.loads(data)
        except json.JSONDecodeError:
            import logging
            logging.getLogger(__name__).warning(
                "Redis 消息数据损坏，丢弃: %s", data[:100]
            )
            return None
        return self._to_langchain_message(
            d["role"], d["content"], d.get("tool_calls"), d.get("tool_call_id")
        )

    def _deserialize_row(self, row) -> BaseMessage:
        return self._to_langchain_message(
            row["role"],
            row["content"],
            row["tool_calls"],
            row["tool_call_id"],
        )

    @staticmethod
    def _to_langchain_message(
        role: str,
        content: str,
        tool_calls=None,
        tool_call_id=None,
    ) -> BaseMessage:
        if role == "user":
            return HumanMessage(content=content)
        elif role == "assistant":
            return AIMessage(content=content, tool_calls=tool_calls or [])
        elif role == "system":
            return SystemMessage(content=content)
        elif role == "tool":
            return ToolMessage(
                content=content, tool_call_id=tool_call_id or ""
            )
        logging.getLogger(__name__).warning(
            "未知消息 role: %s，降级为 HumanMessage", role
        )
        return HumanMessage(content=content)

    # ------------------------------------------------------------------ #
    # 会话管理
    # ------------------------------------------------------------------ #

    async def get_sessions(self, user_id: int) -> list[dict]:
        """查询用户会话列表（排除已删除）。"""
        async with db_pools.echomusic.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT session_id, title, context_summary, is_pinned,
                       create_time, update_time
                FROM ai_sessions
                WHERE user_id = $1 AND is_deleted = FALSE
                ORDER BY is_pinned DESC, update_time DESC
                """,
                user_id,
            )
        return [dict(r) for r in rows]

    async def create_session(
        self, user_id: int, title: Optional[str] = None
    ) -> str:
        """创建新会话，返回 session_id（UUID 字符串）。"""
        async with db_pools.echomusic.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ai_sessions (user_id, title)
                VALUES ($1, $2)
                RETURNING session_id
                """,
                user_id,
                title,
            )
        return str(row["session_id"])

    async def soft_delete_session(self, session_id: str, user_id: int) -> bool:
        """软删除会话，返回是否成功。"""
        async with db_pools.echomusic.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE ai_sessions
                SET is_deleted = TRUE, update_time = CURRENT_TIMESTAMP
                WHERE session_id = $1 AND user_id = $2
                """,
                session_id,
                user_id,
            )
        return "UPDATE 1" in result

    async def get_session_messages(
        self, session_id: str, user_id: int, page_num: int = 1, page_size: int = 20
    ) -> list[dict]:
        """分页读取会话历史消息（按时间倒序，最新在前）。"""
        offset = (page_num - 1) * page_size
        async with db_pools.echomusic.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT m.id, m.role, m.content, m.tool_calls, m.tool_call_id, m.create_time
                FROM ai_messages m
                INNER JOIN ai_sessions s ON m.session_id = s.session_id
                WHERE m.session_id = $1 AND s.user_id = $2
                ORDER BY m.create_time ASC
                LIMIT $3 OFFSET $4
                """,
                session_id,
                user_id,
                page_size,
                offset,
            )
        return [dict(r) for r in rows]

    async def update_session_title(self, session_id: str, title: str):
        """更新会话标题。"""
        async with db_pools.echomusic.acquire() as conn:
            await conn.execute(
                """
                UPDATE ai_sessions
                SET title = $1, update_time = CURRENT_TIMESTAMP
                WHERE session_id = $2
                """,
                title,
                session_id,
            )

    async def update_context_summary(self, session_id: str, summary: str):
        """更新会话长期记忆摘要。"""
        async with db_pools.echomusic.acquire() as conn:
            await conn.execute(
                """
                UPDATE ai_sessions
                SET context_summary = $1, update_time = CURRENT_TIMESTAMP
                WHERE session_id = $2
                """,
                summary,
                session_id,
            )

    async def get_context_summary(self, session_id: str) -> str | None:
        """获取会话的长期记忆摘要。"""
        async with db_pools.echomusic.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT context_summary FROM ai_sessions WHERE session_id = $1",
                session_id,
            )
        return row["context_summary"] if row else None

    async def get_message_count(self, session_id: str) -> int:
        """获取会话消息总数。"""
        async with db_pools.echomusic.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT COUNT(*) FROM ai_messages WHERE session_id = $1",
                session_id,
            )
        return row["count"]

    # ------------------------------------------------------------------ #
    # 摘要与标题
    # ------------------------------------------------------------------ #

    async def generate_summary(self, session_id: str) -> Optional[str]:
        """
        生成会话长期记忆摘要。
        仅在消息数超过阈值且尚未生成摘要时调用。
        任何异常均被捕获，避免影响主对话流程。
        """
        try:
            async with db_pools.echomusic.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT context_summary FROM ai_sessions WHERE session_id = $1
                    """,
                    session_id,
                )
                if row and row["context_summary"]:
                    return None  # 已存在，不重复生成

                count = await conn.fetchrow(
                    "SELECT COUNT(*) FROM ai_messages WHERE session_id = $1",
                    session_id,
                )
                if count["count"] < self.SUMMARY_THRESHOLD:
                    return None

                messages = await conn.fetch(
                    """
                    SELECT role, content FROM ai_messages
                    WHERE session_id = $1
                    ORDER BY create_time ASC
                    """,
                    session_id,
                )

            # 构造摘要提示
            history = "\n".join(
                [f"{m['role']}: {m['content'][:100]}" for m in messages]
            )
            summary_prompt = (
                f"请用一句话概括以下对话的主题（20字以内）：\n\n{history}"
            )

            summary = await llm_service.achat(
                [
                    SystemMessage(content="你是一个对话摘要生成助手。"),
                    HumanMessage(content=summary_prompt),
                ]
            )
            summary = summary.strip()[:500]
            await self.update_context_summary(session_id, summary)
            return summary
        except Exception:
            # 摘要生成失败不影响主流程，静默返回 None
            return None

    async def auto_title(self, session_id: str, first_message: str) -> str:
        """
        根据首条用户消息自动生成会话标题。
        异步调用，不阻塞主回复。
        """
        prompt = (
            f"请用5-10个字概括以下用户问题的主题，不要加引号：\n\n"
            f"{first_message[:200]}"
        )
        try:
            title = await llm_service.achat(
                [
                    SystemMessage(content="你是一个标题生成助手。"),
                    HumanMessage(content=prompt),
                ]
            )
            title = title.strip().replace('"', "").replace("'", "")[:100]
            await self.update_session_title(session_id, title)
            return title
        except Exception:
            # 标题生成失败不抛异常，保持默认空标题
            return ""

    # ------------------------------------------------------------------ #
    # Redis 缓存管理
    # ------------------------------------------------------------------ #

    async def clear_redis_memory(self, user_id: int, session_id: str):
        """清理指定会话的 Redis 缓存。"""
        redis_key = f"{self.REDIS_PREFIX}:{user_id}:{session_id}"
        await redis_client.client.delete(redis_key)

    async def heartbeat(self, user_id: int, session_id: str):
        """续期 Redis 缓存 TTL。"""
        redis_key = f"{self.REDIS_PREFIX}:{user_id}:{session_id}"
        await redis_client.client.expire(redis_key, self.REDIS_TTL)


# 全局单例
memory_service = MemoryService()
