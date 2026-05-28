```sql
CREATE TABLE forum_replies(
    id          SERIAL PRIMARY KEY,
    post_id     INT       NOT NULL,               -- 所属帖子ID
    user_id     INT       NOT NULL,               -- 回复用户ID
    content     TEXT         NOT NULL,        
    likecount     INTEGER      NOT NULL DEFAULT 0,  -- 点赞数
    comment_count BIGINT         NOT NULL DEFAULT 0,  -- 评论数
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    
    CONSTRAINT fk_replies_post_id
        FOREIGN KEY (post_id) REFERENCES forum_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_replies_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_forum_replies_post_time 
    ON forum_replies(post_id, created_at DESC);

```
