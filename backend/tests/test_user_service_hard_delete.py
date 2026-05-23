"""UserService.hard_delete_user 级联清理单元测试。"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.user_service import UserService


class TestHardDeleteUser:
    """测试硬删除用户的级联清理逻辑。"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return UserService(mock_db)

    @pytest.fixture
    def admin_user(self):
        user = MagicMock()
        user.id = 99
        user.permission = 1
        return user

    @patch("app.services.user_service.user_crud")
    @patch("app.services.user_service.forum_zone_crud")
    @patch("app.services.user_service.ai_conversation_crud")
    @patch("app.services.user_service.comment_crud")
    @patch("app.services.user_service.forum_post_crud")
    @patch("app.services.user_service.forum_reply_crud")
    @patch("app.services.user_service.user_favorite_crud")
    @patch("app.services.user_service.delete_file_from_oss_sync")
    @patch("app.services.user_service.convert_oss_url_to_file_path")
    @patch("app.services.user_service.get_sync_redis_client")
    @patch("app.services.user_service.delete_checkpoint", new_callable=MagicMock)
    @patch("app.services.user_service.asyncio.run")
    def test_cascade_delete_all_associations(
        self,
        mock_asyncio_run,
        mock_delete_checkpoint,
        mock_get_sync_redis,
        mock_convert_oss,
        mock_delete_oss_sync,
        mock_user_fav_crud,
        mock_forum_reply_crud,
        mock_forum_post_crud,
        mock_comment_crud,
        mock_ai_conv_crud,
        mock_forum_zone_crud,
        mock_user_crud,
        service,
        admin_user,
    ):
        """正常场景：用户有头像、区主身份、对话、评论、帖子、回复、收藏等，全部级联清理。"""
        target_user = MagicMock()
        target_user.id = 42
        target_user.avatar_url = "https://oss.example.com/avatars/42.png"
        target_user.is_deleted = False
        mock_user_crud.get_user_by_id.return_value = target_user
        mock_user_crud.hard_delete_user.return_value = 1

        # 模拟 AI 对话
        conv = MagicMock()
        conv.id = 100
        mock_ai_conv_crud.list_ai_conversations_by_user.return_value = ([conv], 1)

        # 模拟评论
        mock_comment_crud.get_comment_ids_by_user_id.return_value = [11, 12]
        mock_comment_crud.get_child_comment_ids_by_parent_ids.return_value = [21]

        # 模拟帖子
        mock_forum_post_crud.get_post_ids_by_user_id.return_value = [31, 32]

        mock_redis = MagicMock()
        mock_get_sync_redis.return_value = mock_redis

        service.hard_delete_user(42, admin_user)

        # 验证头像删除
        mock_convert_oss.assert_called_once_with(target_user.avatar_url)
        mock_delete_oss_sync.assert_called_once()

        # 验证区主转移
        mock_forum_zone_crud.update_zones_manager_by_old_manager.assert_called_once_with(
            service.db, 42, admin_user.id, auto_commit=False
        )

        # 验证 AI 对话删除
        mock_ai_conv_crud.delete_ai_conversation.assert_called_once_with(
            service.db, 100, auto_commit=False
        )
        mock_delete_checkpoint.assert_called_once_with("100")
        mock_asyncio_run.assert_called_once()

        # 验证评论清理：先删点赞，再删评论（含子评论）
        mock_comment_crud.delete_comment_likes_by_comment_ids.assert_called_once_with(
            service.db, [11, 12, 21], auto_commit=False
        )
        mock_comment_crud.delete_comments_by_ids.assert_called_once_with(
            service.db, [11, 12, 21], auto_commit=False
        )

        # 验证论坛内容清理：先删帖子下的回复，再删帖子，最后删用户自己的回复
        mock_forum_reply_crud.delete_replies_by_post_ids.assert_called_once_with(
            service.db, [31, 32], auto_commit=False
        )
        assert mock_forum_post_crud.delete_post.call_count == 2
        mock_forum_reply_crud.delete_replies_by_user_id.assert_called_once_with(
            service.db, 42, auto_commit=False
        )

        # 验证收藏/关注清理
        mock_user_fav_crud.delete_all_favorites_by_user_id.assert_called_once_with(
            service.db, 42, auto_commit=False
        )

        # 验证 Redis 清理
        mock_redis.delete.assert_called_once_with("user_revoked:42")

        # 验证最终删除用户
        mock_user_crud.hard_delete_user.assert_called_once_with(
            service.db, 42, auto_commit=False
        )

    @patch("app.services.user_service.user_crud")
    def test_user_not_found(self, mock_user_crud, service, admin_user):
        """用户不存在时应抛出 404。"""
        mock_user_crud.get_user_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.hard_delete_user(999, admin_user)

        assert exc_info.value.status_code == 404
        assert "用户不存在" in exc_info.value.detail

    @patch("app.services.user_service.user_crud")
    @patch("app.services.user_service.delete_file_from_oss_sync")
    @patch("app.services.user_service.get_sync_redis_client")
    def test_user_without_avatar(
        self,
        mock_get_sync_redis,
        mock_delete_oss_sync,
        mock_user_crud,
        service,
        admin_user,
    ):
        """用户没有头像时不应调用 OSS 删除。"""
        target_user = MagicMock()
        target_user.id = 42
        target_user.avatar_url = None
        mock_user_crud.get_user_by_id.return_value = target_user
        mock_user_crud.hard_delete_user.return_value = 1
        mock_get_sync_redis.return_value = MagicMock()

        service.hard_delete_user(42, admin_user)

        mock_delete_oss_sync.assert_not_called()
        mock_user_crud.hard_delete_user.assert_called_once()

    @patch("app.services.user_service.user_crud")
    @patch("app.services.user_service.comment_crud")
    @patch("app.services.user_service.forum_post_crud")
    @patch("app.services.user_service.forum_reply_crud")
    @patch("app.services.user_service.user_favorite_crud")
    @patch("app.services.user_service.get_sync_redis_client")
    def test_user_with_no_associations(
        self,
        mock_get_sync_redis,
        mock_user_fav_crud,
        mock_forum_reply_crud,
        mock_forum_post_crud,
        mock_comment_crud,
        mock_user_crud,
        service,
        admin_user,
    ):
        """用户没有任何关联数据时，空列表不应触发批量删除。"""
        target_user = MagicMock()
        target_user.id = 42
        target_user.avatar_url = None
        mock_user_crud.get_user_by_id.return_value = target_user
        mock_user_crud.hard_delete_user.return_value = 1

        mock_comment_crud.get_comment_ids_by_user_id.return_value = []
        mock_comment_crud.get_child_comment_ids_by_parent_ids.return_value = []
        mock_forum_post_crud.get_post_ids_by_user_id.return_value = []

        mock_get_sync_redis.return_value = MagicMock()

        service.hard_delete_user(42, admin_user)

        # 空列表时不应调用批量删除
        mock_comment_crud.delete_comment_likes_by_comment_ids.assert_not_called()
        mock_comment_crud.delete_comments_by_ids.assert_not_called()
        mock_forum_reply_crud.delete_replies_by_post_ids.assert_not_called()
        mock_forum_post_crud.delete_post.assert_not_called()

        mock_user_crud.hard_delete_user.assert_called_once()

    @patch("app.services.user_service.user_crud")
    @patch("app.services.user_service.delete_file_from_oss_sync")
    @patch("app.services.user_service.forum_zone_crud")
    @patch("app.services.user_service.get_sync_redis_client")
    def test_critical_cleanup_failure_aborts_delete(
        self,
        mock_get_sync_redis,
        mock_forum_zone_crud,
        mock_delete_oss_sync,
        mock_user_crud,
        service,
        admin_user,
    ):
        """关键数据库清理步骤失败时应中止硬删除。"""
        target_user = MagicMock()
        target_user.id = 42
        target_user.avatar_url = "https://oss.example.com/avatars/42.png"
        mock_user_crud.get_user_by_id.return_value = target_user

        # 头像删除失败属于非关键步骤，不应中断流程
        mock_delete_oss_sync.side_effect = RuntimeError("OSS error")
        # 关键步骤失败（区主管理转移）应中断硬删除
        mock_forum_zone_crud.update_zones_manager_by_old_manager.side_effect = RuntimeError(
            "DB error"
        )
        mock_get_sync_redis.return_value = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            service.hard_delete_user(42, admin_user)
        assert exc_info.value.status_code == 500
        assert "关键清理步骤失败" in exc_info.value.detail
        mock_user_crud.hard_delete_user.assert_not_called()
