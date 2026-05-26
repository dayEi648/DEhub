1. 启用 pgvector 扩展（每个数据库只需执行一次）

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. 建表

```sql
CREATE TABLE openapi_endpoint_embeddings (
    id            SERIAL PRIMARY KEY,
    document_id   INT NOT NULL REFERENCES openapi_documents(id) ON DELETE CASCADE,
    chunk_id      VARCHAR(255) NOT NULL UNIQUE,
    path          VARCHAR(500) NOT NULL,
    method        VARCHAR(10) NOT NULL,
    summary       VARCHAR(500),
    description   VARCHAR(2000),
    tags          JSONB,
    operation_id  VARCHAR(255),
    content       TEXT NOT NULL,
    embedding     vector(1024) NOT NULL,
    content_hash  VARCHAR(32),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

3. 索引

```sql
-- HNSW 索引（余弦相似度）
CREATE INDEX idx_openapi_endpoint_embeddings_hnsw
ON openapi_endpoint_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 查询过滤索引
CREATE INDEX idx_openapi_endpoint_embeddings_document_id
    ON openapi_endpoint_embeddings(document_id);
CREATE INDEX idx_openapi_endpoint_embeddings_method
    ON openapi_endpoint_embeddings(method);
```

4. 触发器：自动维护 updated_at

```sql
CREATE TRIGGER trigger_openapi_endpoint_embeddings_updated_at
    BEFORE UPDATE ON openapi_endpoint_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

5. 说明

- `document_id`：外键指向 `openapi_documents.id`，级联删除。删除文档时自动清理其下所有端点向量。
- `chunk_id`：端点分片全局唯一标识，格式建议为 `ep_{index}_{method}_{path}_{document_id}`。
- `path`：API 路径，如 `/api/v1/users`。
- `method`：HTTP 方法，大写存储（GET、POST 等）。
- `content`：用于 RAG 的端点文本，由解析服务生成。
- `embedding`：pgvector 向量，维度与配置 `EMBEDDING_DIMENSION_EFFECTIVE` 一致（默认 1024）。
- `content_hash`：端点内容 MD5 hash，用于去重避免重复 embedding。
- `tags`：OpenAPI tags，JSONB 数组存储。
