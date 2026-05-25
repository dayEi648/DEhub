from app.services.blog_post_service import BlogPostService


def test_get_blog_post_returns_incremented_view_count(
    db_session,
    blog_post,
    normal_user,
):
    blog_post.view_count = 0
    db_session.commit()
    db_session.expire_all()

    response = BlogPostService(db_session).get_blog_post(blog_post.id, normal_user)

    assert response.view_count == 1
