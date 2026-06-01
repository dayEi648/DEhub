"""验证 comment_count 同步修复"""
import pytest
from app.schemas.comment import CommentCreate
from app.crud import comment as comment_crud
from app.models.blog_post import BlogPost


def test_create_comment_increments_blog_post_comment_count(db_session, blog_post, normal_user):
    """创建博客评论后，blog_post.comment_count 应 +1"""
    db = db_session
    bp = db.query(BlogPost).filter(BlogPost.id == blog_post.id).first()
    initial_count = bp.comment_count

    comment_in = CommentCreate(target_type="blog_post", target_id=blog_post.id, content="测试评论")
    new_comment = comment_crud.create_comment(db, comment_in, normal_user.id)

    db.refresh(bp)
    assert bp.comment_count == initial_count + 1

    # 清理
    comment_crud.delete_comment(db, new_comment.id)
    db.refresh(bp)
    assert bp.comment_count == initial_count


def test_delete_comment_decrements_blog_post_comment_count(db_session, blog_post, normal_user):
    """删除博客评论后，blog_post.comment_count 应 -1"""
    db = db_session

    comment_in = CommentCreate(target_type="blog_post", target_id=blog_post.id, content="待删除测试")
    new_comment = comment_crud.create_comment(db, comment_in, normal_user.id)

    bp = db.query(BlogPost).filter(BlogPost.id == blog_post.id).first()
    count_after_create = bp.comment_count

    comment_crud.delete_comment(db, new_comment.id)
    db.refresh(bp)

    assert bp.comment_count == count_after_create - 1


def test_delete_comments_by_ids_batch_decrements_count(db_session, blog_post, normal_user):
    """批量删除评论时，comment_count 应正确减少"""
    db = db_session

    # 创建3条评论
    comments = []
    for i in range(3):
        comment_in = CommentCreate(target_type="blog_post", target_id=blog_post.id, content=f"批量测试{i}")
        comments.append(comment_crud.create_comment(db, comment_in, normal_user.id))

    bp = db.query(BlogPost).filter(BlogPost.id == blog_post.id).first()
    assert bp.comment_count == 3

    # 批量删除其中2条
    comment_crud.delete_comments_by_ids(db, [comments[0].id, comments[1].id])
    db.refresh(bp)
    assert bp.comment_count == 1

    # 删除最后1条
    comment_crud.delete_comments_by_ids(db, [comments[2].id])
    db.refresh(bp)
    assert bp.comment_count == 0
