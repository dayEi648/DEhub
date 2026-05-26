1. 自动更新字段
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

2. 自动维护评论点赞关系
```sql
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
```

3. 自动维护评论目标计数字段
```sql
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
```
