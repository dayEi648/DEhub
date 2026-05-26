```sql
-- 关注分区表（用户可关注论坛分区，以便快速进入或获取更新）
CREATE TABLE user_zone_follows (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    zone_id     INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 一个用户只能关注同一分区一次
    CONSTRAINT uq_user_zone_follows
        UNIQUE (user_id, zone_id),

    CONSTRAINT fk_uzf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_uzf_zone
        FOREIGN KEY (zone_id) REFERENCES forum_zones(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- 查询某用户关注的分区列表（按关注时间倒序）
CREATE INDEX idx_uzf_user ON user_zone_follows(user_id, created_at DESC);
-- 查询某分区被哪些用户关注
CREATE INDEX idx_uzf_zone ON user_zone_follows(zone_id);
```
