import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.comment_service import CommentService
from app.schemas.comment import CommentCreate


class TestCommentServiceCreate:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return CommentService(db)

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.id = 1
        user.permission = 0
        return user

    @pytest.fixture
    def comment_in(self):
        return CommentCreate(
            target_type="blog_post",
            target_id=1,
            content="测试评论",
        )

    def test_create_comment_success(self, service, normal_user, comment_in):
        """正常创建评论应成功并返回带 user 的对象"""
        with patch(
            "app.services.comment_service.blog_post_crud.get_blog_post_by_id",
            return_value=MagicMock(),
        ):
            with patch(
                "app.services.comment_service.comment_crud.create_comment"
            ) as mock_create:
                with patch(
                    "app.services.comment_service.comment_crud.get_comment_by_id"
                ) as mock_get:
                    created = MagicMock()
                    created.id = 10
                    mock_create.return_value = created
                    mock_get.return_value = MagicMock(id=10)

                    result = service.create_comment(comment_in, normal_user)
                    assert result.id == 10
                    mock_create.assert_called_once()
                    mock_get.assert_called_once()

    def test_create_comment_invalid_target_type(self, service, normal_user):
        """非法 target_type 应 400"""
        comment_in = CommentCreate(
            target_type="invalid_type",
            target_id=1,
            content="测试评论",
        )
        with pytest.raises(HTTPException) as exc_info:
            service.create_comment(comment_in, normal_user)
        assert exc_info.value.status_code == 400
        assert "不支持" in exc_info.value.detail

    def test_create_comment_target_not_found(self, service, normal_user, comment_in):
        """目标实体不存在应 404"""
        with patch(
            "app.services.comment_service.blog_post_crud.get_blog_post_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.create_comment(comment_in, normal_user)
            assert exc_info.value.status_code == 404
            assert "不存在" in exc_info.value.detail


class TestCommentServiceDelete:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return CommentService(db)

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.id = 1
        user.permission = 0
        return user

    @pytest.fixture
    def admin_user(self):
        user = MagicMock()
        user.id = 2
        user.permission = 1
        return user

    @pytest.fixture
    def other_user(self):
        user = MagicMock()
        user.id = 3
        user.permission = 0
        return user

    def test_delete_by_owner(self, service, normal_user):
        """作者删除自己的评论应成功"""
        comment = MagicMock()
        comment.user_id = 1
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.delete_comment",
                return_value=1,
            ) as mock_delete:
                service.delete_comment(1, normal_user)
                mock_delete.assert_called_once()

    def test_delete_by_admin(self, service, admin_user):
        """管理员删除他人评论应成功"""
        comment = MagicMock()
        comment.user_id = 1
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.delete_comment",
                return_value=1,
            ) as mock_delete:
                service.delete_comment(1, admin_user)
                mock_delete.assert_called_once()

    def test_delete_by_other_user(self, service, other_user):
        """普通用户删除他人评论应 403"""
        comment = MagicMock()
        comment.user_id = 1
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.delete_comment(1, other_user)
            assert exc_info.value.status_code == 403
            assert "无权" in exc_info.value.detail

    def test_delete_comment_not_found(self, service, normal_user):
        """评论不存在应 404"""
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.delete_comment(1, normal_user)
            assert exc_info.value.status_code == 404


class TestCommentServiceLike:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return CommentService(db)

    @pytest.fixture
    def normal_user(self):
        user = MagicMock()
        user.id = 1
        return user

    def test_like_success(self, service, normal_user):
        """正常点赞应成功"""
        comment = MagicMock()
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.get_user_comment_like",
                return_value=None,
            ):
                with patch(
                    "app.services.comment_service.comment_crud.create_user_comment_like"
                ) as mock_create:
                    service.like_comment(1, normal_user)
                    mock_create.assert_called_once()

    def test_like_already_liked(self, service, normal_user):
        """重复点赞应 400"""
        comment = MagicMock()
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.get_user_comment_like",
                return_value=MagicMock(),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    service.like_comment(1, normal_user)
                assert exc_info.value.status_code == 400
                assert "已点赞" in exc_info.value.detail

    def test_like_comment_not_found(self, service, normal_user):
        """点赞不存在的评论应 404"""
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                service.like_comment(1, normal_user)
            assert exc_info.value.status_code == 404

    def test_unlike_success(self, service, normal_user):
        """正常取消点赞应成功"""
        comment = MagicMock()
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.get_user_comment_like",
                return_value=MagicMock(),
            ):
                with patch(
                    "app.services.comment_service.comment_crud.delete_user_comment_like"
                ) as mock_delete:
                    service.unlike_comment(1, normal_user)
                    mock_delete.assert_called_once()

    def test_unlike_not_liked(self, service, normal_user):
        """未点赞时取消点赞应 400"""
        comment = MagicMock()
        with patch(
            "app.services.comment_service.comment_crud.get_comment_by_id",
            return_value=comment,
        ):
            with patch(
                "app.services.comment_service.comment_crud.get_user_comment_like",
                return_value=None,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    service.unlike_comment(1, normal_user)
                assert exc_info.value.status_code == 400
                assert "未点赞" in exc_info.value.detail


class TestCommentServiceList:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        return CommentService(db)

    def test_list_by_time(self, service):
        """按时间排序应透传参数"""
        with patch(
            "app.services.comment_service.comment_crud.get_comments",
            return_value=([], 0),
        ) as mock_get:
            service.list_comments("blog_post", 1, None, "time", 0, 20)
            call_args = mock_get.call_args
            assert call_args.kwargs["sort_by"] == "time"

    def test_list_by_hot(self, service):
        """按热度排序应透传参数"""
        with patch(
            "app.services.comment_service.comment_crud.get_comments",
            return_value=([], 0),
        ) as mock_get:
            service.list_comments("blog_post", 1, None, "hot", 0, 20)
            call_args = mock_get.call_args
            assert call_args.kwargs["sort_by"] == "hot"
