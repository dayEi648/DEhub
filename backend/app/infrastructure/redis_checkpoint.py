import json
import logging
from typing import Any, AsyncIterator

from langchain_core.messages import messages_from_dict, messages_to_dict
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    RunnableConfig,
)

from app.core.config import settings
from app.redis_client import get_redis_client

logger = logging.getLogger(__name__)

_KEY_PREFIX = "lg:ckpt"


def _build_key(thread_id: str) -> str:
    return f"{_KEY_PREFIX}:{thread_id}"


def _serialize_checkpoint(checkpoint: Checkpoint) -> str:
    """
    将 Checkpoint 序列化为 JSON 字符串。

    特殊处理 channel_values["messages"]，使用 LangChain 的 messages_to_dict。
    """
    data = dict(checkpoint)
    channel_values = dict(data.get("channel_values", {}))
    if "messages" in channel_values:
        channel_values["messages"] = messages_to_dict(channel_values["messages"])
    data["channel_values"] = channel_values
    return json.dumps(data, ensure_ascii=False, default=str)


def _deserialize_checkpoint(raw: str | bytes) -> Checkpoint:
    """
    从 JSON 字符串反序列化为 Checkpoint。

    特殊处理 channel_values["messages"]，使用 LangChain 的 messages_from_dict。
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    data = json.loads(raw)
    channel_values = dict(data.get("channel_values", {}))
    if "messages" in channel_values:
        channel_values["messages"] = messages_from_dict(channel_values["messages"])
    data["channel_values"] = channel_values
    return Checkpoint(
        v=data["v"],
        id=data["id"],
        ts=data["ts"],
        channel_values=channel_values,
        channel_versions=data.get("channel_versions", {}),
        versions_seen=data.get("versions_seen", {}),
        updated_channels=data.get("updated_channels"),
    )


class RedisCheckpointSaver(BaseCheckpointSaver):
    """
    基于 Redis 的 LangGraph Checkpointer。

    使用 Redis String 存储每个 thread 的最新 Checkpoint，
    支持 TTL 自动过期，与现有 Redis 缓存策略一致。

    Key 格式: lg:ckpt:{thread_id}
    TTL: settings.REDIS_CHAT_HISTORY_TTL (默认 1800 秒)
    """

    def __init__(self, ttl: int | None = None) -> None:
        super().__init__()
        self._redis = get_redis_client()
        self._ttl = ttl or settings.REDIS_CHAT_HISTORY_TTL

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------

    def _get_thread_id(self, config: RunnableConfig) -> str:
        """从 RunnableConfig 中提取 thread_id。"""
        configurable = config.get("configurable") or {}
        thread_id = configurable.get("thread_id")
        if not thread_id:
            raise ValueError("RunnableConfig 中缺少 thread_id")
        return str(thread_id)

    # ------------------------------------------------------------------
    # 核心接口实现
    # ------------------------------------------------------------------

    async def aget(self, config: RunnableConfig) -> Checkpoint | None:
        """获取指定 thread 的最新 Checkpoint。"""
        thread_id = self._get_thread_id(config)
        key = _build_key(thread_id)
        try:
            raw = await self._redis.get(key)
            if not raw:
                return None
            return _deserialize_checkpoint(raw)
        except Exception as e:
            logger.warning("RedisCheckpointSaver aget failed for %s: %s", key, e)
            return None

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Any,
    ) -> RunnableConfig:
        """保存 Checkpoint 到 Redis，覆盖该 thread 的旧版本。"""
        thread_id = self._get_thread_id(config)
        key = _build_key(thread_id)
        try:
            payload = _serialize_checkpoint(checkpoint)
            pipe = self._redis.pipeline()
            pipe.set(key, payload)
            pipe.expire(key, self._ttl)
            await pipe.execute()
        except Exception as e:
            logger.warning("RedisCheckpointSaver aput failed for %s: %s", key, e)

        # 返回更新后的 config（携带 checkpoint_id）
        return {
            **config,
            "configurable": {
                **(config.get("configurable") or {}),
                "checkpoint_id": checkpoint["id"],
                "checkpoint_ns": "",
            },
        }

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """获取 CheckpointTuple（含 parent_config）。

        Redis 实现只保留最新版本，因此 parent_config 始终为 None。
        """
        checkpoint = await self.aget(config)
        if checkpoint is None:
            return None
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata={},
            parent_config=None,
            pending_writes=[],
        )

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """列出 Checkpoint 版本。

        Redis 实现只保留单个最新版本，因此最多 yield 一条记录。
        """
        if config is None:
            return
        checkpoint = await self.aget(config)
        if checkpoint is None:
            return
        yield CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata={},
            parent_config=None,
            pending_writes=[],
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Any,
        task_id: str,
        task_path: str = "",
    ) -> None:
        """保存中间写入（writes）。

        当前实现暂不需要持久化 writes，直接忽略。
        若后续需要支持断点续传，可扩展为单独 Redis Key 存储。
        """
        # 空实现：writes 在 LangGraph 中用于断点续传和并发控制，
        # 对于对话场景，只需最终 checkpoint 即可恢复状态。
        pass

    # ------------------------------------------------------------------
    # 扩展：清理指定 thread 的 checkpoint
    # ------------------------------------------------------------------

    async def delete_checkpoint(self, thread_id: str) -> None:
        """删除指定 thread 的 checkpoint（对话删除时调用）。"""
        key = _build_key(thread_id)
        try:
            await self._redis.delete(key)
            logger.info("Deleted checkpoint for thread %s", thread_id)
        except Exception as e:
            logger.warning("RedisCheckpointSaver delete failed for %s: %s", key, e)
