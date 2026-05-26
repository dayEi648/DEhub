```sql
CREATE TABLE forum_posts (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(128) NOT NULL,
    content     TEXT NOT NULL,
    user_id     INT NOT NULL,
    zone_id     INT NOT NULL,
    view_count  BIGINT NOT NULL DEFAULT 0,
    reply_count BIGINT NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_posts_zone_id 
        FOREIGN KEY (zone_id) REFERENCES forum_zones(id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_posts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_posts_reply_count_nonnegative
        CHECK (reply_count >= 0)
);

-- 查询某用户发布的帖子
CREATE INDEX idx_posts_user_id ON forum_posts(user_id);
-- 分区下按时间排序
CREATE INDEX idx_posts_zone_created ON forum_posts(zone_id, created_at DESC);
-- 分区下观看量排序
CREATE INDEX idx_posts_zone_view ON forum_posts(zone_id, view_count DESC);

-- 自动维护updated_at
CREATE TRIGGER trg_posts_set_updated_at
    BEFORE UPDATE ON forum_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

```
