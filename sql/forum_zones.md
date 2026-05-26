```sql
-- 论坛分区表
CREATE TABLE forum_zones (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(255) NOT NULL,
    zone_name   VARCHAR(64) NOT NULL,
    description TEXT,
    manager_id  INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_zones_slug UNIQUE (slug),
    CONSTRAINT fk_zones_manager_id
        FOREIGN KEY (manager_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- slug查询极频繁
CREATE INDEX idx_zones_slug ON forum_zones(slug);

```
