```sql
CREATE TABLE content_moderation_records (
    id                  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id             VARCHAR(64) NOT NULL UNIQUE,
    trace_id            VARCHAR(64),
    target_type         VARCHAR(32) NOT NULL,
    target_id           INTEGER NOT NULL,
    target_version      VARCHAR(64) NOT NULL,
    trigger_action      VARCHAR(20) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    risk_level          VARCHAR(20) NOT NULL DEFAULT 'none',
    categories          JSONB,
    original_snapshot   JSONB NOT NULL,
    moderation_result   JSONB,
    action_plan         JSONB,
    action_result       JSONB,
    model_name          VARCHAR(50),
    error_type          VARCHAR(50),
    error_message       TEXT,
    created_by_user_id  INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at          TIMESTAMP WITH TIME ZONE,
    finished_at         TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_cm_record_version UNIQUE (target_type, target_id, target_version),
    CONSTRAINT fk_cm_record_user FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_cm_record_trace FOREIGN KEY (trace_id) REFERENCES agent_traces(trace_id) ON DELETE SET NULL
);

CREATE INDEX idx_cm_records_target ON content_moderation_records(target_type, target_id, created_at DESC);
CREATE INDEX idx_cm_records_status ON content_moderation_records(status, created_at DESC);
CREATE INDEX idx_cm_records_trace ON content_moderation_records(trace_id);
CREATE INDEX idx_cm_records_task ON content_moderation_records(task_id);
```

## 字段说明

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PK, 自增 | 主键 |
| `task_id` | VARCHAR(64) | NOT NULL, UNIQUE | 任务 UUID，幂等标识 |
| `trace_id` | VARCHAR(64) | FK → agent_traces.trace_id, ON DELETE SET NULL | 关联 Agent trace |
| `target_type` | VARCHAR(32) | NOT NULL | 目标类型：`user`/`blog_post`/`forum_zone`/`forum_post`/`forum_reply`/`comment` |
| `target_id` | INTEGER | NOT NULL | 目标对象 ID |
| `target_version` | VARCHAR(64) | NOT NULL | 内容版本指纹（通常为目标对象的 `updated_at` ISO 格式） |
| `trigger_action` | VARCHAR(20) | NOT NULL | 触发动作：`create`/`update`/`publish`/`retry` |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `'pending'` | 审核状态 |
| `risk_level` | VARCHAR(20) | NOT NULL, DEFAULT `'none'` | 风险等级：`none`/`low`/`medium`/`high` |
| `categories` | JSONB | 可空 | 命中分类列表，如 `["辱骂", "广告"]` |
| `original_snapshot` | JSONB | NOT NULL | 审核时的字段快照 |
| `moderation_result` | JSONB | 可空 | 模型结构化输出 |
| `action_plan` | JSONB | 可空 | 处置计划 |
| `action_result` | JSONB | 可空 | 处置执行结果 |
| `model_name` | VARCHAR(50) | 可空 | 使用的模型名称 |
| `error_type` | VARCHAR(50) | 可空 | 错误类型 |
| `error_message` | TEXT | 可空 | 错误详情 |
| `created_by_user_id` | INTEGER | FK → users.id, ON DELETE SET NULL | 触发审核的用户 |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | 创建时间 |
| `started_at` | TIMESTAMPTZ | 可空 | 审核开始时间 |
| `finished_at` | TIMESTAMPTZ | 可空 | 审核结束时间 |

## 索引说明

| 索引名 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| `idx_cm_records_target` | `(target_type, target_id, created_at DESC)` | 复合索引 | 按目标对象查询历史记录 |
| `idx_cm_records_status` | `(status, created_at DESC)` | 复合索引 | 按状态筛选 |
| `idx_cm_records_trace` | `(trace_id)` | 单列索引 | 关联 Agent trace 查询 |
| `idx_cm_records_task` | `(task_id)` | 单列索引, UNIQUE | 幂等任务查询 |

## 唯一约束

| 约束名 | 字段 | 说明 |
|--------|------|------|
| `uq_cm_record_version` | `(target_type, target_id, target_version)` | 同一版本的内容只能有一条非失败状态的审核记录 |
| `content_moderation_records_task_id_key` | `(task_id)` | 每个任务 ID 全局唯一 |

## 外键约束

| 约束名 | 字段 | 引用 | 删除行为 |
|--------|------|------|----------|
| `fk_cm_record_user` | `created_by_user_id` | `users(id)` | SET NULL |
| `fk_cm_record_trace` | `trace_id` | `agent_traces(trace_id)` | SET NULL |
