import pytest
from pydantic import ValidationError

from app.schemas.comment import CommentCreate, CommentResponse, CommentUserInfo
from app.models.comment import Comment
from app.models.user_comment_like import UserCommentLike


class TestCommentSchema:
    def test_create_valid(self):
        """正常创建请求应通过校验"""
        comment = CommentCreate(
            target_type="blog_post",
            target_id=1,
            content="这是一条评论",
        )
        assert comment.target_type == "blog_post"
        assert comment.target_id == 1
        assert comment.parent_id is None
        assert comment.content == "这是一条评论"

    def test_create_with_parent(self):
        """带 parent_id 的创建请求应通过校验"""
        comment = CommentCreate(
            target_type="blog_post",
            target_id=1,
            parent_id=5,
            content="回复评论",
        )
        assert comment.parent_id == 5

    def test_create_content_empty_rejected(self):
        """空内容应被拒绝"""
        with pytest.raises(ValidationError):
            CommentCreate(
                target_type="blog_post",
                target_id=1,
                content="",
            )

    def test_create_target_id_zero_rejected(self):
        """target_id 小于 1 应被拒绝"""
        with pytest.raises(ValidationError):
            CommentCreate(
                target_type="blog_post",
                target_id=0,
                content="评论",
            )

    def test_response_with_user(self):
        """响应模型应支持嵌套用户信息"""
        data = {
            "id": 1,
            "target_type": "blog_post",
            "target_id": 1,
            "parent_id": None,
            "user_id": 2,
            "content": "评论内容",
            "likecount": 5,
            "created_at": "2025-01-01T00:00:00+00:00",
            "user": {
                "id": 2,
                "username": "testuser",
                "avatar_url": None,
            },
        }
        resp = CommentResponse.model_validate(data)
        assert resp.id == 1
        assert resp.user.username == "testuser"

    def test_comment_user_info(self):
        """精简用户信息模型应正确解析"""
        user = CommentUserInfo(id=1, username="user", avatar_url="https://example.com/a.jpg")
        assert user.id == 1
        assert user.avatar_url == "https://example.com/a.jpg"


class TestCommentModel:
    def test_content_not_nullable(self):
        """content 字段应不允许为 NULL"""
        col = Comment.__table__.c.content
        assert col.nullable is False

    def test_likecount_default(self):
        """likecount 应有默认值 0"""
        col = Comment.__table__.c.likecount
        assert col.default is not None
        assert col.default.arg == 0

    def test_parent_id_nullable(self):
        """parent_id 应允许为 NULL"""
        col = Comment.__table__.c.parent_id
        assert col.nullable is True


class TestUserCommentLikeModel:
    def test_comment_id_not_nullable(self):
        """comment_id 应不允许为 NULL"""
        col = UserCommentLike.__table__.c.comment_id
        assert col.nullable is False

    def test_user_id_not_nullable(self):
        """user_id 应不允许为 NULL"""
        col = UserCommentLike.__table__.c.user_id
        assert col.nullable is False
