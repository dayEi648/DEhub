```sql
-- 创建评论表
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,
    target_type     VARCHAR(32)  NOT NULL,        -- 目标类型
    target_id       INT          NOT NULL,        -- 目标ID
    parent_id       INT          NULL,            -- 父级ID（逻辑外键：博客场景指向comments.id，论坛场景指向forum_replies.id）
    user_id         INT          NOT NULL,        -- 评论用户ID
    content         TEXT         NOT NULL,        -- 评论内容
    is_nested       BOOLEAN      NOT NULL DEFAULT FALSE,  -- 是否为嵌套回复
    nested_parent_id INT         NULL,            -- 嵌套回复所回复的里层/回复评论ID
    likecount       INT          NOT NULL DEFAULT 0,  -- 点赞数
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- 创建时间
    
    -- nested_parent_id 始终指向 comments.id 里的里层/回复评论
    CONSTRAINT fk_comments_nested_parent 
        FOREIGN KEY (nested_parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引1：加速查询某目标下的评论，并支持按时间排序
CREATE INDEX idx_comments_target_time 
    ON comments(target_type, target_id, created_at DESC);

-- 索引2：加速查询某父级下的子评论（按是否嵌套+时间排序）
CREATE INDEX idx_comments_parent_nested 
    ON comments(parent_id, is_nested, created_at DESC);

-- 索引3：加速按点赞数排序，并支持按时间排序
CREATE INDEX idx_comments_target_likes 
    ON comments(target_type, target_id, likecount DESC);

-- 索引4：单独加速按时间排序的全局时间线查询
CREATE INDEX idx_comments_created_at 
    ON comments(created_at DESC);

-- 索引5：加速查询某评论被哪些嵌套回复引用
CREATE INDEX idx_comments_nested_parent_time
    ON comments(nested_parent_id, created_at DESC);
```
