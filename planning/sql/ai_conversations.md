```sql
--  AI 对话元数据表
CREATE TABLE ai_conversations (
    id              SERIAL PRIMARY KEY,
    user_id         INT NOT NULL,
    title           VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMPTZ,

    CONSTRAINT fk_ai_conversations_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 查某用户最近对话
CREATE INDEX idx_ai_conversations_user_created
    ON ai_conversations(user_id, created_at DESC);

-- 绑定触发器
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```
