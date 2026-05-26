1. 建表
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
```

2. 索引
```sql
CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN (tags);
CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at DESC);
CREATE INDEX idx_blog_posts_category_id ON blog_posts(category_id);
CREATE INDEX idx_blog_posts_published_created_at
    ON blog_posts(created_at DESC)
    WHERE status = 'published';
```

3. 触发器：自动维护 updated_at
```sql
CREATE TRIGGER trigger_blog_posts_updated_at
    BEFORE UPDATE ON blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

