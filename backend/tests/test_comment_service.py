"""CommentService 评论系统重构单元测试（嵌套回复与计数）"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate, CommentResponse


class TestCommentServiceCreate:
    """测试评论创建校验逻辑"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return CommentService(mock_db)

    @pytest.fixture
    def current_user(self):
        user = MagicMock()
        user.id = 1
        user.permission = 0
        return user

    @patch("app.services.comment_service.blog_post_crud")
    def test_create_blog_surface_comment_success(self, mock_blog_crud, service, current_user):
        """博客表层评论：parent_id=None, is_nested=False"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=None,
            is_nested=False,
            nested_parent_id=None,
            content="表层评论",
        )

        with patch.object(service, "_validate_comment_create", wraps=service._validate_comment_create):
            with patch("app.services.comment_service.comment_crud") as mock_comment_crud:
                mock_comment = MagicMock()
                mock_comment_crud.create_comment.return_value = mock_comment
                mock_comment_crud.get_comment_by_id.return_value = mock_comment
                result = service.create_comment(comment_in, current_user)
                assert result is mock_comment

    @patch("app.services.comment_service.blog_post_crud")
    def test_create_blog_nested_without_parent_rejected(self, mock_blog_crud, service, current_user):
        """博客嵌套回复必须带 parent_id"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=None,
            is_nested=True,
            nested_parent_id=10,
            content="非法嵌套",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, current_user)
        assert exc_info.value.status_code == 400

    @patch("app.services.comment_service.blog_post_crud")
    def test_create_comment_with_embedded_image_rejected(self, mock_blog_crud, service, current_user):
        """评论内容不允许内嵌图片语法"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=None,
            is_nested=False,
            nested_parent_id=None,
            content="这里有图 ![alt](https://example.com/a.png)",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, current_user)
        assert exc_info.value.status_code == 400
        assert "不支持内嵌图片" in exc_info.value.detail

    @patch("app.services.comment_service.blog_post_crud")
    @patch("app.services.comment_service.comment_crud")
    def test_create_blog_inner_reply_success(
        self, mock_comment_crud, mock_blog_crud, service, current_user
    ):
        """博客里层回复：parent_id=表层评论ID, is_nested=False"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        parent_comment = MagicMock()
        parent_comment.id = 10
        parent_comment.parent_id = None
        parent_comment.target_type = "blog_post"
        parent_comment.target_id = 1
        mock_comment_crud.get_comment_by_id.return_value = parent_comment

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=10,
            is_nested=False,
            nested_parent_id=None,
            content="里层回复",
        )

        mock_new = MagicMock()
        mock_comment_crud.create_comment.return_value = mock_new
        # 第一次 get_comment_by_id 用于校验 parent，第二次用于刷新
        mock_comment_crud.get_comment_by_id.side_effect = [parent_comment, mock_new]

        result = service.create_comment(comment_in, current_user)
        assert result is mock_new

    @patch("app.services.comment_service.blog_post_crud")
    @patch("app.services.comment_service.comment_crud")
    def test_create_blog_nested_reply_success(
        self, mock_comment_crud, mock_blog_crud, service, current_user
    ):
        """博客嵌套回复：parent_id=表层ID, is_nested=True, nested_parent_id=里层ID"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        surface = MagicMock()
        surface.id = 10
        surface.parent_id = None
        surface.target_type = "blog_post"
        surface.target_id = 1

        inner = MagicMock()
        inner.id = 20
        inner.is_nested = False
        inner.target_type = "blog_post"
        inner.target_id = 1
        inner.parent_id = 10

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=10,
            is_nested=True,
            nested_parent_id=20,
            content="嵌套回复",
        )

        mock_new = MagicMock()
        mock_comment_crud.create_comment.return_value = mock_new
        # 依次：校验 parent(10) → 校验 nested_parent(20) → 刷新新评论
        mock_comment_crud.get_comment_by_id.side_effect = [surface, inner, mock_new]

        result = service.create_comment(comment_in, current_user)
        assert result is mock_new

    @patch("app.services.comment_service.blog_post_crud")
    @patch("app.services.comment_service.comment_crud")
    def test_create_blog_nested_to_wrong_surface_rejected(
        self, mock_comment_crud, mock_blog_crud, service, current_user
    ):
        """嵌套回复的 nested_parent_id 必须与 parent_id 指向同一表层评论"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        surface_a = MagicMock()
        surface_a.id = 10
        surface_a.parent_id = None
        surface_a.target_type = "blog_post"
        surface_a.target_id = 1

        inner_b = MagicMock()
        inner_b.id = 20
        inner_b.is_nested = False
        inner_b.target_type = "blog_post"
        inner_b.target_id = 1
        inner_b.parent_id = 99  # 属于另一表层评论

        def side_effect(db, cid):
            if cid == 10:
                return surface_a
            if cid == 20:
                return inner_b
            return None

        mock_comment_crud.get_comment_by_id.side_effect = side_effect

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=10,
            is_nested=True,
            nested_parent_id=20,
            content="非法嵌套",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, current_user)
        assert exc_info.value.status_code == 400
        assert "同一表层评论" in exc_info.value.detail

    @patch("app.services.comment_service.forum_reply_crud")
    def test_create_forum_reply_comment_auto_parent(self, mock_reply_crud, service, current_user):
        """论坛场景未传 parent_id 时自动设为 target_id"""
        mock_reply_crud.get_reply_by_id.return_value = MagicMock()

        with patch("app.services.comment_service.comment_crud") as mock_comment_crud:
            mock_new = MagicMock()
            mock_comment_crud.create_comment.return_value = mock_new
            mock_comment_crud.get_comment_by_id.return_value = mock_new

            comment_in = CommentCreate(
                target_type="forum_reply",
                target_id=5,
                parent_id=None,
                is_nested=False,
                nested_parent_id=None,
                content="论坛回复",
            )
            result = service.create_comment(comment_in, current_user)
            # 验证 create_comment 被调用时 parent_id 已自动补全
            call_args = mock_comment_crud.create_comment.call_args[0][1]
            assert call_args.parent_id == 5

    @patch("app.services.comment_service.forum_reply_crud")
    def test_create_forum_reply_parent_must_equal_target(self, mock_reply_crud, service, current_user):
        """论坛场景 parent_id 必须等于 target_id"""
        mock_reply_crud.get_reply_by_id.return_value = MagicMock()

        comment_in = CommentCreate(
            target_type="forum_reply",
            target_id=5,
            parent_id=99,
            is_nested=False,
            nested_parent_id=None,
            content="非法",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, current_user)
        assert exc_info.value.status_code == 400
        assert "parent_id 必须等于 target_id" in exc_info.value.detail

    @patch("app.services.comment_service.blog_post_crud")
    @patch("app.services.comment_service.comment_crud")
    def test_create_non_nested_with_nested_parent_rejected(
        self, mock_comment_crud, mock_blog_crud, service, current_user
    ):
        """非嵌套回复不能带 nested_parent_id"""
        mock_blog_crud.get_blog_post_by_id.return_value = MagicMock()

        comment_in = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=10,
            is_nested=False,
            nested_parent_id=20,
            content="非法",
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, current_user)
        assert exc_info.value.status_code == 400
        assert "不能指定 nested_parent_id" in exc_info.value.detail


class TestCommentServiceDelete:
    """测试评论删除级联逻辑"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return CommentService(mock_db)

    @pytest.fixture
    def current_user(self):
        user = MagicMock()
        user.id = 1
        user.permission = 0
        return user

    @patch("app.services.comment_service.comment_crud")
    def test_delete_blog_surface_cascades_children(self, mock_comment_crud, service, current_user):
        """删除博客表层评论时级联删除子评论"""
        surface = MagicMock()
        surface.id = 10
        surface.user_id = 1
        surface.target_type = "blog_post"
        surface.parent_id = None
        mock_comment_crud.get_comment_by_id.return_value = surface

        child1 = MagicMock()
        child1.id = 11
        child2 = MagicMock()
        child2.id = 12
        mock_comment_crud.get_comments_by_parent_id.return_value = [child1, child2]

        service.delete_comment(10, current_user)

        # 验证先删子评论点赞、再删子评论、最后删表层
        mock_comment_crud.delete_comment_likes_by_comment_ids.assert_called_once_with(
            service.db, [11, 12]
        )
        mock_comment_crud.delete_comments_by_ids.assert_called_once_with(
            service.db, [11, 12]
        )
        mock_comment_crud.delete_comment.assert_called_once_with(service.db, 10)

    @patch("app.services.comment_service.comment_crud")
    def test_delete_blog_inner_no_children(self, mock_comment_crud, service, current_user):
        """删除博客里层回复（无子评论）直接删除"""
        inner = MagicMock()
        inner.id = 11
        inner.user_id = 1
        inner.target_type = "blog_post"
        inner.parent_id = 10
        mock_comment_crud.get_comment_by_id.return_value = inner
        mock_comment_crud.get_comments_by_parent_id.return_value = []

        service.delete_comment(11, current_user)

        mock_comment_crud.delete_comment_likes_by_comment_ids.assert_not_called()
        mock_comment_crud.delete_comments_by_ids.assert_not_called()
        mock_comment_crud.delete_comment.assert_called_once_with(service.db, 11)


class TestCommentServiceList:
    """测试评论列表查询参数透传"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return CommentService(mock_db)

    @patch("app.services.comment_service.comment_crud")
    def test_list_comments_passes_new_params(self, mock_comment_crud, service):
        """is_nested 和 nested_parent_id 正确透传给 CRUD"""
        mock_comment_crud.get_comments.return_value = ([], 0)

        service.list_comments(
            target_type="blog_post",
            target_id=1,
            parent_id=10,
            is_nested=True,
            nested_parent_id=20,
            sort_by="time",
            skip=0,
            limit=20,
        )

        call_kwargs = mock_comment_crud.get_comments.call_args[1]
        assert call_kwargs["is_nested"] is True
        assert call_kwargs["nested_parent_id"] == 20
        assert call_kwargs["parent_id"] == 10

    @patch("app.services.comment_service.comment_crud")
    def test_list_comments_with_like_state(self, mock_comment_crud, service):
        """批量点赞状态在 Service 层组装，返回 CommentResponse 列表。"""
        comment_1 = MagicMock()
        comment_1.id = 1
        comment_2 = MagicMock()
        comment_2.id = 2
        mock_comment_crud.get_comments.return_value = ([comment_1, comment_2], 2)

        current_user = MagicMock()
        current_user.id = 100
        mock_comment_crud.get_user_liked_comment_ids.return_value = {2}

        with patch.object(CommentResponse, "model_validate", side_effect=[MagicMock(id=1, is_liked=False), MagicMock(id=2, is_liked=False)]):
            items, total = service.list_comments_with_like_state(
                target_type="blog_post",
                target_id=10,
                parent_id=None,
                is_nested=None,
                nested_parent_id=None,
                sort_by="time",
                skip=0,
                limit=20,
                current_user=current_user,
            )

        assert total == 2
        assert items[0].is_liked is False
        assert items[1].is_liked is True
        mock_comment_crud.get_user_liked_comment_ids.assert_called_once_with(
            service.db, 100, [1, 2]
        )


class TestForumReplyServiceDelete:
    """测试 ForumReplyService 删除时级联清理评论"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        from app.services.forum_reply_service import ForumReplyService
        return ForumReplyService(mock_db)

    @pytest.fixture
    def current_user(self):
        user = MagicMock()
        user.id = 1
        user.permission = 0
        return user

    @patch("app.services.forum_reply_service.forum_reply_crud")
    @patch("app.services.forum_reply_service.forum_post_crud")
    @patch("app.services.forum_reply_service.comment_crud")
    @patch("app.services.forum_reply_service.is_zone_manager")
    @patch("app.services.forum_reply_service.extract_oss_image_urls_from_markdown")
    @patch("app.services.forum_reply_service.convert_oss_url_to_file_path")
    @patch("app.services.forum_reply_service.delete_file_from_oss_sync")
    def test_delete_reply_cascades_comments(
        self,
        mock_delete_file,
        mock_convert_path,
        mock_extract_urls,
        mock_is_manager,
        mock_comment_crud,
        mock_post_crud,
        mock_reply_crud,
        service,
        current_user,
    ):
        """删除 forum_reply 时先删除其下所有评论"""
        reply = MagicMock()
        reply.id = 5
        reply.user_id = 1
        reply.post_id = 100
        reply.content = "reply content"
        mock_reply_crud.get_reply_by_id.return_value = reply
        mock_is_manager.return_value = False
        mock_extract_urls.return_value = ["https://oss.example.com/forum/replies/20260101/a.jpg"]
        mock_convert_path.return_value = "forum/replies/20260101/a.jpg"

        comment1 = MagicMock()
        comment1.id = 21
        comment2 = MagicMock()
        comment2.id = 22
        mock_comment_crud.get_comments.return_value = ([comment1, comment2], 2)

        service.delete_reply(5, current_user)

        mock_comment_crud.get_comments.assert_called_once_with(
            service.db, target_type="forum_reply", target_id=5, limit=10000
        )
        mock_comment_crud.delete_comment_likes_by_comment_ids.assert_called_once_with(
            service.db, [21, 22]
        )
        mock_comment_crud.delete_comments_by_ids.assert_called_once_with(
            service.db, [21, 22]
        )
        mock_extract_urls.assert_called_once_with("reply content")
        mock_convert_path.assert_called_once_with("https://oss.example.com/forum/replies/20260101/a.jpg")
        mock_delete_file.assert_called_once_with("forum/replies/20260101/a.jpg")
        mock_reply_crud.delete_reply.assert_called_once_with(service.db, 5)
        mock_post_crud.decrement_reply_count.assert_called_once_with(service.db, 100)

    @patch("app.services.forum_reply_service.forum_reply_crud")
    @patch("app.services.forum_reply_service.forum_post_crud")
    @patch("app.services.forum_reply_service.comment_crud")
    @patch("app.services.forum_reply_service.is_zone_manager")
    @patch("app.services.forum_reply_service.extract_oss_image_urls_from_markdown")
    @patch("app.services.forum_reply_service.convert_oss_url_to_file_path")
    @patch("app.services.forum_reply_service.delete_file_from_oss_sync")
    def test_delete_reply_db_failure_should_not_delete_oss_files(
        self,
        mock_delete_file,
        mock_convert_path,
        mock_extract_urls,
        mock_is_manager,
        mock_comment_crud,
        mock_post_crud,
        mock_reply_crud,
        service,
        current_user,
    ):
        reply = MagicMock()
        reply.id = 5
        reply.user_id = 1
        reply.post_id = 100
        reply.content = "reply content"
        mock_reply_crud.get_reply_by_id.return_value = reply
        mock_is_manager.return_value = False
        mock_extract_urls.return_value = ["https://oss.example.com/forum/replies/a.jpg"]
        mock_convert_path.return_value = "forum/replies/a.jpg"
        mock_comment_crud.get_comments.return_value = ([], 0)
        mock_reply_crud.delete_reply.side_effect = RuntimeError("db failed")

        with pytest.raises(RuntimeError):
            service.delete_reply(5, current_user)

        mock_delete_file.assert_not_called()
