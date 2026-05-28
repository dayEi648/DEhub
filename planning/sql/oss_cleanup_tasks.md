1. 建表

```sql
CREATE TABLE oss_cleanup_tasks (
    id            SERIAL PRIMARY KEY,
    file_path     VARCHAR(512) NOT NULL,
    source        VARCHAR(100) NOT NULL,
    status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending', 'succeeded', 'failed')),
    retry_count   INT NOT NULL DEFAULT 0,
    last_error    TEXT,
    next_retry_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

2. 索引

```sql
CREATE INDEX idx_oss_cleanup_tasks_status_next_retry
    ON oss_cleanup_tasks(status, next_retry_at);
CREATE INDEX idx_oss_cleanup_tasks_created_at
    ON oss_cleanup_tasks(created_at DESC);
```

3. 说明

- `file_path`：OSS 对象路径，不保存完整外链，便于幂等删除。
- `source`：登记清理任务的业务来源，例如 `user.avatar`、`blog.cover`、`forum.post.delete`。
- `status`：任务状态。`pending` 表示已登记未处理；`succeeded` 表示删除成功或文件已不存在；`failed` 表示删除失败，等待后续重试。
- `retry_count`：失败重试次数。
- `last_error`：最近一次删除失败的错误信息。
- `next_retry_at`：下次可重试时间，避免失败后立即高频重试。
- 该表用于承接数据库事务提交后的 OSS 清理副作用，避免 OSS 删除失败时只留下日志、无法追踪和重试。
