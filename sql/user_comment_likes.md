```sql
-- 评论点赞表
CREATE TABLE user_comment_likes (
    id          SERIAL PRIMARY KEY,
    comment_id  INT          NOT NULL,
    user_id     INT          NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 一个用户对一条评论只能点一次赞
    CONSTRAINT uq_user_comment_likes_user 
        UNIQUE (comment_id, user_id),
    
    CONSTRAINT fk_user_comment_likes_comment 
        FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_comment_likes_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 点赞表索引
CREATE INDEX idx_user_comment_likes_user 
    ON user_comment_likes(user_id, created_at DESC);  -- 查某用户赞过哪些评论

CREATE INDEX idx_user_comment_likes_created 
    ON user_comment_likes(created_at DESC);           -- 最新点赞动态
    
-- 触发器自动维护
CREATE TRIGGER trg_user_comment_likes_insert
    AFTER INSERT ON user_comment_likes
    FOR EACH ROW EXECUTE FUNCTION update_comment_likecount();

CREATE TRIGGER trg_user_comment_likes_delete
    AFTER DELETE ON user_comment_likes
    FOR EACH ROW EXECUTE FUNCTION update_comment_likecount();
```