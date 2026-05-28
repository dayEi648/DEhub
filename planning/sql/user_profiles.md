## user_profiles

用户画像表（普通表，非向量表）。

每个用户仅保留一条画像记录，对话时拼接到 SystemMessage 中注入 AI 上下文。
画像内容由 small 模型根据对话历史判断并更新。

---

1. 建表

```sql
CREATE TABLE user_profiles (
    user_id      INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    profile_text TEXT NOT NULL DEFAULT '',
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

2. 索引

```sql
-- 无需额外索引，user_id 已是主键
```

> 设计说明：
> - `profile_text`：用户画像文本（由 small LLM 生成，第三人称简洁描述）
> - `ON DELETE CASCADE`：用户注销时画像自动级联清理
> - `updated_at`：记录画像最后更新时间
> - 单用户单条记录：使用 `UPSERT`（INSERT ... ON CONFLICT）进行更新
