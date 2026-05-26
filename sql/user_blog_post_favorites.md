```sql
-- 博客文章收藏表（任何用户均可收藏博客文章）
CREATE TABLE user_blog_post_favorites (
    id           SERIAL PRIMARY KEY,
    user_id      INT NOT NULL,
    blog_post_id INT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 一个用户对同一篇文章只能收藏一次
    CONSTRAINT uq_user_blog_post_favorites
        UNIQUE (user_id, blog_post_id),

    CONSTRAINT fk_ubpf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ubpf_blog_post
        FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 查询某用户收藏的文章列表（按收藏时间倒序）
CREATE INDEX idx_ubpf_user ON user_blog_post_favorites(user_id, created_at DESC);
-- 查询某文章被哪些人收藏
CREATE INDEX idx_ubpf_blog_post ON user_blog_post_favorites(blog_post_id);
```
