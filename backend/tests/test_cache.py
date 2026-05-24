"""缓存基础设施单元测试。"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ConfigDict

from app.infrastructure.cache import (
    CACHE_KEY_PREFIX,
    CACHE_TAG_PREFIX,
    acquire_cache_lock,
    build_cache_key,
    get_json_cache,
    invalidate_cache_tags,
    release_cache_lock,
    set_json_cache,
)


class _DummyItem(BaseModel):
    """测试用模型。"""

    id: int
    name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class _DummyListResponse(BaseModel):
    """测试用列表响应模型。"""

    items: list[_DummyItem]
    total: int

    model_config = ConfigDict(from_attributes=True)


class TestBuildCacheKey:
    """测试缓存 key 生成。"""

    def test_params_order_insensitive(self):
        """相同参数不同顺序应生成相同 key。"""
        key1 = build_cache_key("blog_posts:list", {"skip": 0, "limit": 10, "q": "test"})
        key2 = build_cache_key("blog_posts:list", {"q": "test", "limit": 10, "skip": 0})
        assert key1 == key2

    def test_none_values_filtered(self):
        """None 值应被过滤，不参与 key 生成。"""
        key1 = build_cache_key("blog_posts:list", {"skip": 0, "limit": 10, "category_id": None})
        key2 = build_cache_key("blog_posts:list", {"skip": 0, "limit": 10})
        assert key1 == key2

    def test_no_params(self):
        """无参时应只返回前缀加命名空间。"""
        key = build_cache_key("blog_categories:list")
        assert key == f"{CACHE_KEY_PREFIX}:blog_categories:list"

    def test_different_params_different_keys(self):
        """不同参数应生成不同 key。"""
        key1 = build_cache_key("blog_posts:list", {"skip": 0, "limit": 10})
        key2 = build_cache_key("blog_posts:list", {"skip": 10, "limit": 10})
        assert key1 != key2


class TestGetJsonCache:
    """测试缓存读取与反序列化。"""

    @patch("app.infrastructure.cache._get_redis")
    def test_miss_returns_none(self, mock_get_redis):
        """未命中时应返回 None。"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", _DummyItem)
        assert result is None

    @patch("app.infrastructure.cache._get_redis")
    def test_hit_single_model(self, mock_get_redis):
        """命中单个 BaseModel 时应正确反序列化。"""
        mock_redis = MagicMock()
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_redis.get.return_value = _DummyItem(id=1, name="test", created_at=now).model_dump_json()
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", _DummyItem)
        assert isinstance(result, _DummyItem)
        assert result.id == 1
        assert result.name == "test"
        assert result.created_at == now

    @patch("app.infrastructure.cache._get_redis")
    def test_hit_list_model(self, mock_get_redis):
        """命中 list[BaseModel] 时应正确反序列化。"""
        mock_redis = MagicMock()
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        items = [
            _DummyItem(id=1, name="a", created_at=now),
            _DummyItem(id=2, name="b", created_at=now),
        ]
        mock_redis.get.return_value = json.dumps([item.model_dump(mode="json") for item in items])
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", list[_DummyItem])
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].name == "b"

    @patch("app.infrastructure.cache._get_redis")
    def test_hit_nested_model(self, mock_get_redis):
        """命中嵌套 BaseModel 响应时应正确反序列化。"""
        mock_redis = MagicMock()
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        response = _DummyListResponse(
            items=[_DummyItem(id=1, name="a", created_at=now)],
            total=1,
        )
        mock_redis.get.return_value = response.model_dump_json()
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", _DummyListResponse)
        assert isinstance(result, _DummyListResponse)
        assert result.total == 1
        assert result.items[0].name == "a"

    @patch("app.infrastructure.cache._get_redis")
    def test_corrupted_data_deletes_key_and_returns_none(self, mock_get_redis):
        """反序列化失败时应删除 key 并返回 None，不抛异常。"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = "not-valid-json"
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", _DummyItem)
        assert result is None
        mock_redis.delete.assert_called_once_with("some:key")

    @patch("app.infrastructure.cache._get_redis")
    def test_redis_exception_returns_none(self, mock_get_redis):
        """Redis 操作异常时应返回 None，不抛异常到业务层。"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("redis down")
        mock_get_redis.return_value = mock_redis

        result = get_json_cache("some:key", _DummyItem)
        assert result is None


class TestSetJsonCache:
    """测试缓存写入。"""

    @patch("app.infrastructure.cache._get_redis")
    def test_set_single_model(self, mock_get_redis):
        """写入单个 BaseModel 时应调用 setex。"""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        item = _DummyItem(id=1, name="test", created_at=datetime.now(timezone.utc))
        set_json_cache("key", item, ttl=60)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        assert call_args[0] == "key"
        # TTL 应在 54~66 之间（±10% jitter）
        assert 54 <= call_args[1] <= 66
        assert json.loads(call_args[2])["name"] == "test"

    @patch("app.infrastructure.cache._get_redis")
    def test_set_list_model(self, mock_get_redis):
        """写入 BaseModel 列表时应调用 setex。"""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        items = [
            _DummyItem(id=1, name="a", created_at=datetime.now(timezone.utc)),
        ]
        set_json_cache("key", items, ttl=60)

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args[0]
        parsed = json.loads(call_args[2])
        assert isinstance(parsed, list)
        assert parsed[0]["name"] == "a"

    @patch("app.infrastructure.cache._get_redis")
    def test_set_with_tags(self, mock_get_redis):
        """写入带 tag 时应登记到 tag set。"""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        item = _DummyItem(id=1, name="test", created_at=datetime.now(timezone.utc))
        set_json_cache("key", item, ttl=60, tags=["blog_posts"])

        tag_key = f"{CACHE_TAG_PREFIX}:blog_posts"
        mock_redis.sadd.assert_called_once_with(tag_key, "key")
        mock_redis.expire.assert_called_with(tag_key, mock_redis.setex.call_args[0][1] + 60)

    @patch("app.infrastructure.cache._get_redis")
    def test_redis_exception_silenced(self, mock_get_redis):
        """Redis 写入异常时应静默处理，不抛异常。"""
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("redis down")
        mock_get_redis.return_value = mock_redis

        item = _DummyItem(id=1, name="test", created_at=datetime.now(timezone.utc))
        # 不应抛异常
        set_json_cache("key", item, ttl=60)


class TestInvalidateCacheTags:
    """测试按标签失效缓存。"""

    @patch("app.infrastructure.cache._get_redis")
    def test_invalidate_deletes_keys_and_tag(self, mock_get_redis):
        """失效 tag 时应删除该 tag 下所有 key 及 tag set 本身。"""
        mock_redis = MagicMock()
        mock_redis.smembers.return_value = {"key1", "key2"}
        mock_get_redis.return_value = mock_redis

        invalidate_cache_tags(["blog_posts"])

        tag_key = f"{CACHE_TAG_PREFIX}:blog_posts"
        mock_redis.smembers.assert_called_once_with(tag_key)
        # 集合遍历顺序不确定，只检查调用了一次且参数包含所有 key 和 tag
        mock_redis.pipeline.return_value.delete.assert_called_once()
        call_args = mock_redis.pipeline.return_value.delete.call_args[0]
        assert set(call_args) == {"key1", "key2", tag_key}
        mock_redis.pipeline.return_value.execute.assert_called_once()

    @patch("app.infrastructure.cache._get_redis")
    def test_invalidate_empty_tag_no_error(self, mock_get_redis):
        """tag set 为空时不应报错。"""
        mock_redis = MagicMock()
        mock_redis.smembers.return_value = set()
        mock_get_redis.return_value = mock_redis

        invalidate_cache_tags(["blog_posts"])

        mock_redis.pipeline.return_value.execute.assert_called_once()

    @patch("app.infrastructure.cache._get_redis")
    def test_redis_exception_silenced(self, mock_get_redis):
        """Redis 失效异常时应静默处理。"""
        mock_redis = MagicMock()
        mock_redis.smembers.side_effect = Exception("redis down")
        mock_get_redis.return_value = mock_redis
        invalidate_cache_tags(["blog_posts"])
        # 不应抛异常


class TestCacheLock:
    """测试缓存重建锁。"""

    @patch("app.infrastructure.cache._get_redis")
    def test_acquire_lock_success(self, mock_get_redis):
        """获取锁成功时应返回 token。"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_get_redis.return_value = mock_redis

        token = acquire_cache_lock("hot:key", ttl=5)
        assert token is not None
        assert isinstance(token, str)
        call_args = mock_redis.set.call_args[1]
        assert call_args["nx"] is True
        assert call_args["ex"] == 5

    @patch("app.infrastructure.cache._get_redis")
    def test_acquire_lock_fail(self, mock_get_redis):
        """获取锁失败时应返回 None。"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = None
        mock_get_redis.return_value = mock_redis

        assert acquire_cache_lock("hot:key") is None

    @patch("app.infrastructure.cache._get_redis")
    def test_release_lock_with_token(self, mock_get_redis):
        """释放锁时 token 一致才删除对应 key。"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"mytoken"
        mock_get_redis.return_value = mock_redis

        release_cache_lock("hot:key", token="mytoken")
        mock_redis.delete.assert_called_once_with("dehub:cachelock:v1:hot:key")

    @patch("app.infrastructure.cache._get_redis")
    def test_release_lock_token_mismatch_no_delete(self, mock_get_redis):
        """token 不一致时不应删除锁。"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"other_token"
        mock_get_redis.return_value = mock_redis

        release_cache_lock("hot:key", token="mytoken")
        mock_redis.delete.assert_not_called()

    @patch("app.infrastructure.cache._get_redis")
    def test_release_lock_no_token_no_op(self, mock_get_redis):
        """token 为 None 时不应操作 Redis。"""
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        release_cache_lock("hot:key", token=None)
        mock_redis.get.assert_not_called()
        mock_redis.delete.assert_not_called()

    @patch("app.infrastructure.cache._get_redis")
    def test_acquire_lock_redis_down_returns_none(self, mock_get_redis):
        """Redis 操作异常时获取锁应返回 None，不抛异常。"""
        mock_redis = MagicMock()
        mock_redis.set.side_effect = Exception("redis down")
        mock_get_redis.return_value = mock_redis
        assert acquire_cache_lock("hot:key") is None
