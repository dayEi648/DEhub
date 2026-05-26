1. 建表

```sql
CREATE TABLE openapi_documents (
    id             SERIAL PRIMARY KEY,
    uploaded_by    INT NOT NULL,
    filename       VARCHAR(255) NOT NULL,
    content_hash   VARCHAR(32) NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',
    endpoint_count INT NOT NULL DEFAULT 0,
    chunk_count    INT NOT NULL DEFAULT 0,
    error_message  VARCHAR(500),
    created_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

2. 索引

```sql
CREATE INDEX idx_openapi_documents_status ON openapi_documents(status);
CREATE INDEX idx_openapi_documents_content_hash ON openapi_documents(content_hash);
CREATE INDEX idx_openapi_documents_created_at ON openapi_documents(created_at DESC);
```

3. 触发器：自动维护 updated_at

```sql
CREATE TRIGGER trigger_openapi_documents_updated_at
    BEFORE UPDATE ON openapi_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

4. 说明

- `uploaded_by`：上传管理员用户 ID，关联 `users.id`（业务层校验，不建外键约束以保持灵活性）。
- `content_hash`：原始文件 MD5 hash，用于重复上传检测。
- `status`：解析状态。`pending` 已创建待解析；`processing` 后台正在解析；`completed` 解析完成；`failed` 解析失败。
- `endpoint_count`：解析出的端点数量（path × method）。
- `chunk_count`：实际写入向量库的端点分片数量（去重后可能与 endpoint_count 不同）。
- `error_message`：解析或向量入库失败时的原因描述。
- 文档记录自身承载解析任务状态，不另设独立 task 表。
