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
