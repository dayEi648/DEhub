1. 启用 pgvector 扩展（每个数据库只需执行一次）

> **Windows 环境**
> 1. 确认 PostgreSQL 版本（如 16）：`pg_config --version`
> 2. 下载对应版本的 pgvector 安装包：
>    - 访问 [pgvector/pgvector GitHub Releases](https://github.com/pgvector/pgvector/releases)
>    - 下载与 PostgreSQL 版本匹配的 `.zip`（如 `pgvector-0.8.0-windows-amd64.zip`）
> 3. 解压后将 `vector.dll` 复制到 PostgreSQL 的 `lib/` 目录
> 4. 将 `vector.control` 和 `vector--*.sql` 复制到 PostgreSQL 的 `share/extension/` 目录
> 5. 重启 PostgreSQL 服务
>
> **WSL / Linux 环境**
> ```bash
> sudo apt install postgresql-16-pgvector   # 根据实际 PostgreSQL 版本调整
> ```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. 建表

```sql
CREATE TABLE blog_post_embeddings (
    id           SERIAL PRIMARY KEY,
    post_id      INT NOT NULL UNIQUE REFERENCES blog_posts(id) ON DELETE CASCADE,
    embedding    vector(1024) NOT NULL,
    content_hash VARCHAR(32),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

3. HNSW 索引（余弦相似度）

```sql
CREATE INDEX idx_blog_post_embeddings_hnsw
ON blog_post_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

4. 触发器：自动维护 updated_at

```sql
CREATE TRIGGER trigger_blog_post_embeddings_updated_at
    BEFORE UPDATE ON blog_post_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```
