```sql
-- 对话消息表
CREATE TABLE conversation_messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL,
    role            VARCHAR(32) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 外键约束：对话删除时级联删除其消息
    CONSTRAINT fk_conversation_messages_conversation
        FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE
);

-- "查某对话的消息并按时间正序展示"
CREATE INDEX idx_conversation_messages_conv_created 
    ON conversation_messages(conversation_id, created_at ASC);
```
