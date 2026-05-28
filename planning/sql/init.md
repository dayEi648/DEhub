# 数据库初始化脚本

> 执行顺序已按外键依赖编排，建议整体按序执行。
> 以下脚本包含全部表，按外键依赖顺序排列，可直接整体执行。

---

## 1. 通用函数

```sql
-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 自动维护评论点赞数
CREATE OR REPLACE FUNCTION update_comment_likecount()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE comments SET likecount = likecount + 1 WHERE id = NEW.comment_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE comments SET likecount = likecount - 1 WHERE id = OLD.comment_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 自动维护评论目标计数字段
CREATE OR REPLACE FUNCTION update_target_comment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.target_type = 'blog_post' THEN
            UPDATE blog_posts SET comment_count = comment_count + 1 WHERE id = NEW.target_id;
        ELSIF NEW.target_type = 'forum_reply' THEN
            UPDATE forum_replies SET comment_count = comment_count + 1 WHERE id = NEW.target_id;
        END IF;
    ELSIF TG_OP = 'DELETE' THEN
        IF OLD.target_type = 'blog_post' THEN
            UPDATE blog_posts SET comment_count = comment_count - 1 WHERE id = OLD.target_id;
        ELSIF OLD.target_type = 'forum_reply' THEN
            UPDATE forum_replies SET comment_count = comment_count - 1 WHERE id = OLD.target_id;
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 自动维护论坛回复点赞数（+1）
CREATE OR REPLACE FUNCTION trg_increment_forum_reply_likecount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE forum_replies SET likecount = likecount + 1 WHERE id = NEW.reply_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 自动维护论坛回复点赞数（-1，不低于 0）
CREATE OR REPLACE FUNCTION trg_decrement_forum_reply_likecount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE forum_replies SET likecount = GREATEST(likecount - 1, 0) WHERE id = OLD.reply_id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
```

---

## 2. 用户表

```sql
CREATE TABLE users (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email             VARCHAR(255) NOT NULL UNIQUE,
    username          VARCHAR(64) NOT NULL UNIQUE,
    hashed_password   VARCHAR(255) NOT NULL,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    permission        SMALLINT DEFAULT 0 NOT NULL CHECK (permission IN (0, 1, 2)),
    is_deleted        BOOLEAN DEFAULT false NOT NULL,
    avatar_url        VARCHAR(255),
    personal_profile  TEXT
);
CREATE INDEX idx_users_username ON users(username);
```

---

## 3. 博客分类表

```sql
CREATE TABLE blog_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) NOT NULL,
    slug        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);
```

---

## 4. 论坛分区表

```sql
CREATE TABLE forum_zones (
    id          SERIAL PRIMARY KEY,
    slug        VARCHAR(255) NOT NULL,
    zone_name   VARCHAR(64) NOT NULL,
    description TEXT,
    manager_id  INT NOT NULL,
    view_count  BIGINT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uk_zones_slug UNIQUE (slug),
    CONSTRAINT fk_zones_manager_id
        FOREIGN KEY (manager_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_zones_slug ON forum_zones(slug);
```

---

## 5. 博客文章表

```sql
CREATE TABLE blog_posts (
    id           SERIAL PRIMARY KEY,
    title        VARCHAR(64) NOT NULL,
    slug         VARCHAR(255) NOT NULL UNIQUE,
    summary      TEXT,
    content_md   TEXT NOT NULL,
    cover_image_url  VARCHAR(255),
    user_id      INT NOT NULL,
    category_id  INT NOT NULL,
    tags         TEXT[] DEFAULT '{}',
    status       VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    view_count    BIGINT DEFAULT 0,
    comment_count BIGINT NOT NULL DEFAULT 0,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_blog_posts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_blog_posts_category_id
        FOREIGN KEY (category_id) REFERENCES blog_categories(id)
);

-- 索引
CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN (tags);
CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at DESC);
CREATE INDEX idx_blog_posts_category_id ON blog_posts(category_id);
CREATE INDEX idx_blog_posts_published_created_at
    ON blog_posts(created_at DESC)
    WHERE status = 'published';

-- 触发器：自动维护 updated_at
CREATE TRIGGER trigger_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 6. 论坛帖子表

```sql
CREATE TABLE forum_posts (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(128) NOT NULL,
    content     TEXT NOT NULL,
    user_id     INT NOT NULL,
    zone_id     INT NOT NULL,
    view_count  BIGINT NOT NULL DEFAULT 0,
    reply_count BIGINT NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_posts_zone_id
        FOREIGN KEY (zone_id) REFERENCES forum_zones(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_posts_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_posts_reply_count_nonnegative
        CHECK (reply_count >= 0)
);

-- 索引
CREATE INDEX idx_posts_user_id ON forum_posts(user_id);
CREATE INDEX idx_posts_zone_created ON forum_posts(zone_id, created_at DESC);
CREATE INDEX idx_posts_zone_view ON forum_posts(zone_id, view_count DESC);

-- 触发器
CREATE TRIGGER trg_posts_set_updated_at
    BEFORE UPDATE ON forum_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 7. 论坛回复表

```sql
CREATE TABLE forum_replies(
    id          SERIAL PRIMARY KEY,
    post_id     INT       NOT NULL,
    user_id     INT       NOT NULL,
    content     TEXT         NOT NULL,
    likecount     INTEGER      NOT NULL DEFAULT 0,
    comment_count BIGINT         NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_replies_post_id
        FOREIGN KEY (post_id) REFERENCES forum_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_replies_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_forum_replies_post_time
    ON forum_replies(post_id, created_at DESC);
```

---

## 8. 评论表

```sql
CREATE TABLE comments (
    id              SERIAL PRIMARY KEY,
    target_type     VARCHAR(32)  NOT NULL,
    target_id       INT          NOT NULL,
    parent_id       INT          NULL,
    user_id         INT          NOT NULL,
    content         TEXT         NOT NULL,
    is_nested       BOOLEAN      NOT NULL DEFAULT FALSE,
    nested_parent_id INT         NULL,
    likecount       INT          NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_comments_nested_parent
        FOREIGN KEY (nested_parent_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT fk_comments_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 索引
CREATE INDEX idx_comments_target_time
    ON comments(target_type, target_id, created_at DESC);
CREATE INDEX idx_comments_parent_nested
    ON comments(parent_id, is_nested, created_at DESC);
CREATE INDEX idx_comments_target_likes
    ON comments(target_type, target_id, likecount DESC);
CREATE INDEX idx_comments_created_at
    ON comments(created_at DESC);
CREATE INDEX idx_comments_nested_parent_time
    ON comments(nested_parent_id, created_at DESC);

-- 触发器：自动维护评论目标计数
CREATE TRIGGER trg_comments_insert_count
    AFTER INSERT ON comments
    FOR EACH ROW EXECUTE FUNCTION update_target_comment_count();

CREATE TRIGGER trg_comments_delete_count
    AFTER DELETE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_target_comment_count();
```

---

## 9. AI 对话表

```sql
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

CREATE INDEX idx_ai_conversations_user_created
    ON ai_conversations(user_id, created_at DESC);

-- 触发器
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON ai_conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 10. 对话消息表

```sql
CREATE TABLE conversation_messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL,
    role            VARCHAR(32) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_conversation_messages_conversation
        FOREIGN KEY (conversation_id) REFERENCES ai_conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_conversation_messages_conv_created
    ON conversation_messages(conversation_id, created_at ASC);
```

---

## 11. pgvector 扩展与向量表

### 10.1 启用扩展

> **Windows 环境**
> 1. 确认 PostgreSQL 版本：`pg_config --version`
> 2. 下载对应版本的 pgvector：访问 [pgvector GitHub Releases](https://github.com/pgvector/pgvector/releases)，下载与 PostgreSQL 版本匹配的 `.zip`
> 3. 解压后将 `vector.dll` 放入 PostgreSQL 的 `lib/` 目录
> 4. 将 `vector.control` 和 `vector--*.sql` 放入 PostgreSQL 的 `share/extension/` 目录
> 5. 重启 PostgreSQL 服务
>
> **WSL / Linux 环境**
> ```bash
> sudo apt install postgresql-16-pgvector   # 根据实际 PostgreSQL 版本调整
> ```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 10.2 博客文章向量表

```sql
CREATE TABLE blog_post_embeddings (
    id           SERIAL PRIMARY KEY,
    post_id      INT NOT NULL UNIQUE REFERENCES blog_posts(id) ON DELETE CASCADE,
    embedding    vector(1024) NOT NULL,
    content_hash VARCHAR(32),
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW 索引（余弦相似度）
CREATE INDEX idx_blog_post_embeddings_hnsw
ON blog_post_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 触发器
CREATE TRIGGER trigger_blog_post_embeddings_updated_at
    BEFORE UPDATE ON blog_post_embeddings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## 11. 用户收藏与关系表

### 11.1 博客文章收藏表

```sql
CREATE TABLE user_blog_post_favorites (
    id           SERIAL PRIMARY KEY,
    user_id      INT NOT NULL,
    blog_post_id INT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_blog_post_favorites
        UNIQUE (user_id, blog_post_id),
    CONSTRAINT fk_ubpf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ubpf_blog_post
        FOREIGN KEY (blog_post_id) REFERENCES blog_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_ubpf_user ON user_blog_post_favorites(user_id, created_at DESC);
CREATE INDEX idx_ubpf_blog_post ON user_blog_post_favorites(blog_post_id);
```

### 11.2 评论点赞表

```sql
CREATE TABLE user_comment_likes (
    id          SERIAL PRIMARY KEY,
    comment_id  INT          NOT NULL,
    user_id     INT          NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_comment_likes_user
        UNIQUE (comment_id, user_id),
    CONSTRAINT fk_user_comment_likes_comment
        FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_comment_likes_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_comment_likes_user
    ON user_comment_likes(user_id, created_at DESC);
CREATE INDEX idx_user_comment_likes_created
    ON user_comment_likes(created_at DESC);

-- 触发器自动维护点赞数
CREATE TRIGGER trg_user_comment_likes_insert
    AFTER INSERT ON user_comment_likes
    FOR EACH ROW EXECUTE FUNCTION update_comment_likecount();

CREATE TRIGGER trg_user_comment_likes_delete
    AFTER DELETE ON user_comment_likes
    FOR EACH ROW EXECUTE FUNCTION update_comment_likecount();
```

### 11.3 帖子收藏表

```sql
CREATE TABLE user_post_favorites (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    post_id     INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_post_favorites
        UNIQUE (user_id, post_id),
    CONSTRAINT fk_upf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_upf_post
        FOREIGN KEY (post_id) REFERENCES forum_posts(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_upf_user ON user_post_favorites(user_id, created_at DESC);
CREATE INDEX idx_upf_post ON user_post_favorites(post_id);
```

### 11.4 关注分区表

```sql
CREATE TABLE user_zone_follows (
    id          SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    zone_id     INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_user_zone_follows
        UNIQUE (user_id, zone_id),
    CONSTRAINT fk_uzf_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_uzf_zone
        FOREIGN KEY (zone_id) REFERENCES forum_zones(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_uzf_user ON user_zone_follows(user_id, created_at DESC);
CREATE INDEX idx_uzf_zone ON user_zone_follows(zone_id);
```

### 11.5 回复点赞表

```sql
CREATE TABLE user_forum_reply_likes (
    id          SERIAL PRIMARY KEY,
    reply_id    INT       NOT NULL,
    user_id     INT       NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_reply_like_reply_id
        FOREIGN KEY (reply_id) REFERENCES forum_replies(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reply_like_user_id
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_user_forum_reply_likes_user
        UNIQUE (reply_id, user_id)
);

-- 触发器：点赞时 likecount + 1
CREATE TRIGGER trg_forum_reply_like_insert
    AFTER INSERT ON user_forum_reply_likes
    FOR EACH ROW
    EXECUTE FUNCTION trg_increment_forum_reply_likecount();

-- 触发器：取消点赞时 likecount - 1（不低于 0）
CREATE TRIGGER trg_forum_reply_like_delete
    AFTER DELETE ON user_forum_reply_likes
    FOR EACH ROW
    EXECUTE FUNCTION trg_decrement_forum_reply_likecount();
```

---

## 12. 系统告警日志表

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

---

## 13. OSS 清理任务表

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

CREATE INDEX idx_oss_cleanup_tasks_status_next_retry
    ON oss_cleanup_tasks(status, next_retry_at);
CREATE INDEX idx_oss_cleanup_tasks_created_at
    ON oss_cleanup_tasks(created_at DESC);
```
