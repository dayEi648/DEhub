"""基于标准 Redis 的 LangGraph Checkpointer（Shallow 模式）。

无需 RedisJSON / RediSearch 模块，仅使用 STRING + EXPIRE。
每个 thread 只保留最新 checkpoint，支持 TTL 自动过期。
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, cast

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    PendingWrite,
)
from langgraph.checkpoint.serde.base import SerializerProtocol
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)

_CKPT_PREFIX = "dehub:ckpt"
_WRITE_PREFIX = "dehub:write"


def _encode_typed(data: Any, serde: SerializerProtocol) -> bytes:
    """将对象序列化为带类型标记的字节串（类型标记长度使用 2 字节存储）。"""
    type_, bytes_data = serde.dumps_typed(data)
    type_bytes = type_.encode("utf-8")
    return len(type_bytes).to_bytes(2, "big") + type_bytes + bytes_data


def _decode_typed(raw: bytes, serde: SerializerProtocol) -> Any:
    """从字节串反序列化对象（类型标记长度使用 2 字节读取）。"""
    type_len = int.from_bytes(raw[:2], "big")
    type_str = raw[2 : 2 + type_len].decode("utf-8")
    bytes_data = raw[2 + type_len :]
    return serde.loads_typed((type_str, bytes_data))


class AsyncRedisCheckpointSaver(BaseCheckpointSaver):
    """异步 Redis Checkpointer（标准 Redis，Shallow 模式）。

    仅保留每个 thread / namespace 的最新 checkpoint。
    所有 key 均带 TTL，不活跃后自动清理。
    """

    def __init__(
        self,
        redis_client: AsyncRedis,
        ttl_seconds: int = 600,
        *,
        serde: Optional[SerializerProtocol] = None,
    ) -> None:
        super().__init__(serde=serde)
        self._redis = redis_client
        self._ttl = ttl_seconds

    # ------------------------------------------------------------------
    # 核心读写
    # ------------------------------------------------------------------

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        """保存最新 checkpoint，覆盖旧数据。"""
        configurable = config["configurable"].copy()
        thread_id = str(configurable.pop("thread_id"))
        checkpoint_ns = configurable.pop("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]

        storage_data = {
            "checkpoint": checkpoint,
            "metadata": metadata,
            "checkpoint_id": checkpoint_id,
        }

        raw = _encode_typed(storage_data, self.serde)
        key = f"{_CKPT_PREFIX}:{thread_id}:{checkpoint_ns}"
        await self._redis.set(key, raw, ex=self._ttl)

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

    async def aget_tuple(
        self, config: RunnableConfig
    ) -> Optional[CheckpointTuple]:
        """读取最新 checkpoint，成功后刷新 TTL。"""
        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        key = f"{_CKPT_PREFIX}:{thread_id}:{checkpoint_ns}"
        raw = await self._redis.get(key)
        if raw is None:
            return None

        # 刷新 TTL
        await self._redis.expire(key, self._ttl)

        storage_data = cast(Dict[str, Any], _decode_typed(raw, self.serde))
        checkpoint = cast(Checkpoint, storage_data["checkpoint"])
        metadata = cast(CheckpointMetadata, storage_data["metadata"])
        checkpoint_id = storage_data["checkpoint_id"]

        pending_writes = await self._load_pending_writes(
            thread_id, checkpoint_ns, checkpoint_id
        )

        config_out: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
            }
        }

        return CheckpointTuple(
            config=config_out,
            checkpoint=checkpoint,
            metadata=metadata,
            parent_config=None,
            pending_writes=pending_writes,
        )

    # ------------------------------------------------------------------
    # Writes（中间节点写入）
    # ------------------------------------------------------------------

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """保存中间 writes，每条独立 key 并带 TTL。"""
        thread_id = str(config["configurable"]["thread_id"])
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        for idx, (channel, value) in enumerate(writes):
            raw = _encode_typed(
                {
                    "task_id": task_id,
                    "task_path": task_path,
                    "channel": channel,
                    "value": value,
                    "idx": idx,
                },
                self.serde,
            )
            key = (
                f"{_WRITE_PREFIX}:{thread_id}:{checkpoint_ns}:"
                f"{checkpoint_id}:{task_id}:{idx}"
            )
            await self._redis.set(key, raw, ex=self._ttl)

    async def _load_pending_writes(
        self, thread_id: str, checkpoint_ns: str, checkpoint_id: str
    ) -> List[PendingWrite]:
        """加载与当前 checkpoint 关联的所有 writes。"""
        pattern = (
            f"{_WRITE_PREFIX}:{thread_id}:{checkpoint_ns}:"
            f"{checkpoint_id}:*"
        )
        keys: list[str | bytes] = []
        async for key in self._redis.scan_iter(match=pattern):
            keys.append(key)

        if not keys:
            return []

        # 刷新 writes TTL
        pipe = self._redis.pipeline()
        for k in keys:
            pipe.expire(k, self._ttl)
        await pipe.execute()

        raw_values = await self._redis.mget(keys)
        writes: List[PendingWrite] = []
        for key, raw in zip(keys, raw_values):
            if raw is None:
                continue
            raw_bytes = raw.encode("utf-8") if isinstance(raw, str) else raw
            write_data = cast(Dict[str, Any], _decode_typed(raw_bytes, self.serde))
            writes.append(
                (
                    write_data["task_id"],
                    write_data["channel"],
                    write_data["value"],
                )
            )
        return writes

    # ------------------------------------------------------------------
    # 列表 / 删除 / 清理
    # ------------------------------------------------------------------

    async def alist(
        self,
        config: Optional[RunnableConfig],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[RunnableConfig] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """Shallow 模式下只返回最新 checkpoint。"""
        if config is not None:
            tup = await self.aget_tuple(config)
            if tup is not None:
                yield tup

    async def adelete_thread(self, thread_id: str) -> None:
        """删除指定 thread 的所有 checkpoint 与 writes。"""
        ckpt_pattern = f"{_CKPT_PREFIX}:{thread_id}:*"
        write_pattern = f"{_WRITE_PREFIX}:{thread_id}:*"

        pipe = self._redis.pipeline()
        async for key in self._redis.scan_iter(match=ckpt_pattern):
            pipe.delete(key)
        async for key in self._redis.scan_iter(match=write_pattern):
            pipe.delete(key)
        await pipe.execute()
        logger.info("Deleted checkpoint & writes for thread %s", thread_id)

    async def adelete_for_runs(self, run_ids: Sequence[str]) -> None:
        """当前业务未使用 run-level 删除。"""
        pass

    async def acopy_thread(
        self, source_thread_id: str, target_thread_id: str
    ) -> None:
        """当前业务未使用 copy。"""
        pass

    async def aprune(
        self,
        thread_ids: Sequence[str],
        *,
        strategy: str = "keep_latest",
    ) -> None:
        """Shallow 模式天然只有一个版本，无需 prune。"""
        pass
