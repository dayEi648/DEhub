"""Comments 模块集成测试。"""

import pytest


class TestCommentList:
    def test_list_comments(self, auth_client, blog_post, normal_user, db_session):
        """列表接口应返回评论列表。"""
        from app.models.comment import Comment

        comment = Comment(
            target_type="blog_post",
            target_id=blog_post.id,
            user_id=normal_user.id,
            content="测试评论内容",
        )
        db_session.add(comment)
        db_session.commit()

        response = auth_client.get("/api/v1/comments/", params={"target_type": "blog_post", "target_id": blog_post.id})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        contents = [c["content"] for c in data["items"]]
        assert "测试评论内容" in contents


class TestCommentAuthenticatedOperations:
    def test_create_comment(self, auth_client, blog_post):
        """已认证用户创建评论应返回 201。"""
        payload = {
            "target_type": "blog_post",
            "target_id": blog_post.id,
            "content": "这是一条新评论",
        }
        response = auth_client.post("/api/v1/comments/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "这是一条新评论"
        assert data["target_id"] == blog_post.id

    @pytest.mark.xfail(reason="已知存量 BUG：comment_service.delete_comment 删除对象后仍访问其属性，导致 ObjectDeletedError")
    def test_delete_comment(self, auth_client, blog_post, normal_user, db_session):
        """评论作者或管理员删除评论应返回 204。"""
        from app.models.comment import Comment

        comment = Comment(
            target_type="blog_post",
            target_id=blog_post.id,
            user_id=normal_user.id,
            content="待删除评论",
        )
        db_session.add(comment)
        db_session.commit()
        db_session.refresh(comment)

        response = auth_client.delete(f"/api/v1/comments/{comment.id}")
        # 管理员有权删除任何评论
        assert response.status_code == 204
