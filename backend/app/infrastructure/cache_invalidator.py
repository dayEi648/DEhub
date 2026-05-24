"""缓存失效封装模块。

将各业务域的缓存失效逻辑集中封装，避免在 Service 层散落硬编码的 tag 名称。
所有方法均为静态方法，便于在 Service 写操作成功后直接调用。
"""

from app.infrastructure.cache import invalidate_cache_tags


class BlogCacheInvalidator:
    """博客相关缓存失效器。"""

    @staticmethod
    def invalidate_blog_posts() -> None:
        """失效博客文章公共列表缓存。"""
        invalidate_cache_tags(["blog_posts"])

    @staticmethod
    def invalidate_blog_categories() -> None:
        """失效博客分类列表缓存。"""
        invalidate_cache_tags(["blog_categories"])

    @staticmethod
    def invalidate_all() -> None:
        """同时失效博客文章与分类缓存（用于可能影响 post_count 的写操作）。"""
        invalidate_cache_tags(["blog_posts", "blog_categories"])


class ForumCacheInvalidator:
    """论坛相关缓存失效器。"""

    @staticmethod
    def invalidate_forum_zones() -> None:
        """失效论坛分区列表与详情缓存。"""
        invalidate_cache_tags(["forum_zones"])

    @staticmethod
    def invalidate_forum_posts(zone_id: int | None = None) -> None:
        """失效论坛帖子列表缓存。

        Args:
            zone_id: 若指定，则同时失效该分区维度的 tag；
                若未指定，仅失效全局 ``forum_posts`` tag。
        """
        tags = ["forum_posts"]
        if zone_id is not None:
            tags.append(f"forum_posts:zone:{zone_id}")
        invalidate_cache_tags(tags)

    @staticmethod
    def invalidate_forum_posts_for_zone_change(
        old_zone_id: int | None, new_zone_id: int | None
    ) -> None:
        """帖子分区变更时，同时失效旧分区与新分区的缓存。

        Args:
            old_zone_id: 原分区 ID。
            new_zone_id: 新分区 ID。
        """
        tags = ["forum_posts"]
        if old_zone_id is not None:
            tags.append(f"forum_posts:zone:{old_zone_id}")
        if new_zone_id is not None and new_zone_id != old_zone_id:
            tags.append(f"forum_posts:zone:{new_zone_id}")
        invalidate_cache_tags(tags)
