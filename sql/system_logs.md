1. 建表

```sql
CREATE TABLE system_logs (
    id          SERIAL PRIMARY KEY,
    level       VARCHAR(10) NOT NULL CHECK (level IN ('WARN', 'ERROR', 'CRITICAL')),
    module      VARCHAR(100),
    message     TEXT NOT NULL,
    exception   TEXT,
    trace_id    VARCHAR(64),
    user_id     INT,
    ip          INET,
    extra       JSONB,
    is_resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMPTZ,
    resolved_by INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

2. 索引

```sql
CREATE INDEX idx_system_logs_level_created
    ON system_logs(level, created_at DESC);
CREATE INDEX idx_system_logs_created_at
    ON system_logs(created_at DESC);
CREATE INDEX idx_system_logs_trace_id
    ON system_logs(trace_id);
CREATE INDEX idx_system_logs_unresolved
    ON system_logs(created_at DESC)
    WHERE is_resolved = FALSE;
```

3. 说明

- `level`：限制为 `WARN`、`ERROR`、`CRITICAL`，仅存储需要关注的日志级别。
- `module`：日志来源模块名，便于快速定位问题边界。
- `trace_id`：请求链路追踪 ID，用于串联同一请求内的多条日志。
- `user_id`：触发该日志的操作用户（可空，不建立外键约束，避免用户删除导致日志丢失）。
- `ip`：使用 PostgreSQL 原生 `INET` 类型，节省空间且支持网段查询。
- `is_resolved` / `resolved_at` / `resolved_by`：支持多管理员协同处理告警，前端监控面板可筛选"未处理"日志。
- `extra`：JSONB 类型，用于存储请求参数、响应状态码、环境变量等结构化上下文数据，辅助问题排查。
- `resolved_by` 不建立外键约束，同理避免处理人账号删除影响历史日志记录。
