```sql
CREATE TABLE blog_categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(64) NOT NULL,
    slug        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
);
```