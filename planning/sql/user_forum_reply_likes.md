```sql
-- 回复点赞表
CREATE TABLE user_forum_reply_likes (
    id          SERIAL PRIMARY KEY,
    reply_id    INT       NOT NULL,
    user_id     INT       NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reply_like_reply_id
        FOREIGN KEY (reply_id) REFERENCES forum_replies(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reply_like_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_user_forum_reply_likes_user
        UNIQUE (reply_id, user_id)
);

-- 触发器：点赞时 likecount + 1
CREATE OR REPLACE FUNCTION trg_increment_forum_reply_likecount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE forum_replies SET likecount = likecount + 1 WHERE id = NEW.reply_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_forum_reply_like_insert
    AFTER INSERT ON user_forum_reply_likes
    FOR EACH ROW
    EXECUTE FUNCTION trg_increment_forum_reply_likecount();

-- 触发器：取消点赞时 likecount - 1（不低于 0）
CREATE OR REPLACE FUNCTION trg_decrement_forum_reply_likecount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE forum_replies SET likecount = GREATEST(likecount - 1, 0) WHERE id = OLD.reply_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_forum_reply_like_delete
    AFTER DELETE ON user_forum_reply_likes
    FOR EACH ROW
    EXECUTE FUNCTION trg_decrement_forum_reply_likecount();
```
