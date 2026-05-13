from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.base import Checkpoint

from app.infrastructure.redis_checkpoint import (
    _serialize_checkpoint,
    _deserialize_checkpoint,
    RedisCheckpointSaver,
)


class TestCheckpointSerialization:
    """测试 Checkpoint 序列化与反序列化"""

    def test_round_trip_with_messages(self):
        """含 messages 的 checkpoint 应能正确序列化/反序列化"""
        checkpoint = Checkpoint(
            v=1,
            id="ckpt-1",
            ts="2024-01-01T00:00:00Z",
            channel_values={
                "messages": [
                    HumanMessage(content="hello"),
                    AIMessage(content="hi"),
                ]
            },
            channel_versions={},
            versions_seen={},
            updated_channels=None,
        )
        serialized = _serialize_checkpoint(checkpoint)
        deserialized = _deserialize_checkpoint(serialized)

        assert deserialized["v"] == 1
        assert deserialized["id"] == "ckpt-1"
        messages = deserialized["channel_values"]["messages"]
        assert len(messages) == 2
        assert messages[0].content == "hello"
        assert messages[1].content == "hi"

    def test_round_trip_without_messages(self):
        """不含 messages 的 checkpoint 也应正确"""
        checkpoint = Checkpoint(
            v=1,
            id="ckpt-1",
            ts="2024-01-01T00:00:00Z",
            channel_values={"foo": "bar"},
            channel_versions={},
            versions_seen={},
            updated_channels=None,
        )
        serialized = _serialize_checkpoint(checkpoint)
        deserialized = _deserialize_checkpoint(serialized)
        assert deserialized["channel_values"]["foo"] == "bar"

    def test_deserialize_from_bytes(self):
        """应支持 bytes 输入"""
        checkpoint = Checkpoint(
            v=1,
            id="ckpt-1",
            ts="2024-01-01T00:00:00Z",
            channel_values={},
            channel_versions={},
            versions_seen={},
            updated_channels=None,
        )
        serialized = _serialize_checkpoint(checkpoint)
        deserialized = _deserialize_checkpoint(serialized.encode("utf-8"))
        assert deserialized["id"] == "ckpt-1"


class TestRedisCheckpointSaver:
    """测试 Redis Checkpointer（使用 mock Redis）"""

    @pytest.fixture
    def mock_redis(self):
        redis = MagicMock()
        redis.get = AsyncMock(return_value=None)
        redis.set = AsyncMock()
        redis.expire = AsyncMock()
        redis.delete = AsyncMock()
        redis.pipeline = MagicMock(return_value=MagicMock(
            execute=AsyncMock(),
            set=MagicMock(),
            expire=MagicMock(),
        ))
        return redis

    @pytest.fixture
    def saver(self, mock_redis):
        with patch("app.infrastructure.redis_checkpoint.get_redis_client", return_value=mock_redis):
            s = RedisCheckpointSaver(ttl=1800)
            s._redis = mock_redis
            return s

    @pytest.mark.asyncio
    async def test_aget_empty(self, saver):
        """无 checkpoint 时应返回 None"""
        config = {"configurable": {"thread_id": "123"}}
        result = await saver.aget(config)
        assert result is None

    @pytest.mark.asyncio
    async def test_aput_and_aget(self, saver, mock_redis):
        """写入后应能读取"""
        config = {"configurable": {"thread_id": "123"}}
        checkpoint = Checkpoint(
            v=1,
            id="ckpt-1",
            ts="2024-01-01T00:00:00Z",
            channel_values={"messages": [HumanMessage(content="test")]},
            channel_versions={},
            versions_seen={},
            updated_channels=None,
        )

        # 模拟写入后读取
        stored_payload = None

        async def mock_get(key):
            return stored_payload

        async def mock_pipe_execute():
            nonlocal stored_payload
            pipe = mock_redis.pipeline.return_value
            # 模拟 pipeline 中 set 被调用
            call_args = pipe.set.call_args
            if call_args:
                stored_payload = call_args[0][1]
            return [True, True]

        mock_redis.get = mock_get
        mock_redis.pipeline.return_value.execute = mock_pipe_execute

        new_config = await saver.aput(config, checkpoint, {}, {})
        assert "checkpoint_id" in new_config.get("configurable", {})

        result = await saver.aget(config)
        assert result is not None
        assert result["id"] == "ckpt-1"

    @pytest.mark.asyncio
    async def test_delete_checkpoint(self, saver, mock_redis):
        """删除 checkpoint"""
        await saver.delete_checkpoint("456")
        mock_redis.delete.assert_called_once()
