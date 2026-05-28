```sql
-- 帖子收藏表（用户可收藏论坛帖子，便于跳转查看）
CREATE TABLE user_post_favorites (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    post_id     INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 一个用户对同一帖子只能收藏一次
    CONSTRAINT uq_user_post_favorites
        UNIQUE (user_id, post_id),

    CONSTRAINT fk_upf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_upf_post
        FOREIGN KEY (post_id) REFERENCES forum_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 查询某用户收藏的帖子列表（按收藏时间倒序）
CREATE INDEX idx_upf_user ON user_post_favorites(user_id, created_at DESC);
-- 查询某帖子被哪些用户收藏
CREATE INDEX idx_upf_post ON user_post_favorites(post_id);
```
