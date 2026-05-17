from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    全局配置类，自动从 ``.env`` 文件加载环境变量。

    提供数据库连接字符串等便捷属性，所有字段均可在环境变量中覆盖。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 30)

    LLM_MAIN_API_KEY: str = Field(default="")
    LLM_MAIN_BASE_URL: str = Field(default="")
    LLM_MAIN_MODEL: str = Field(default="")
    LLM_MAIN_MAX_TOKENS: int = Field(default=800000)
    LLM_MAIN_TEMPERATURE: float = Field(default=0.6)
    LLM_MAIN_TIMEOUT: int = Field(default=60)
    LLM_SMALL_API_KEY: str = Field(default="")
    LLM_SMALL_BASE_URL: str = Field(default="")
    LLM_SMALL_MODEL: str = Field(default="")
    LLM_SMALL_MAX_TOKENS: int = Field(default=500000)
    LLM_SMALL_TEMPERATURE: float = Field(default=0.6)
    LLM_SMALL_TIMEOUT: int = Field(default=60)

    EMBEDDING_API_KEY: str = Field(default="")
    EMBEDDING_BASE_URL: str = Field(default="")
    EMBEDDING_MODEL: str = Field(default="")
    EMBEDDING_DIMENSION: int | None = Field(default=1024)
    EMBEDDING_TIMEOUT: int = Field(default=60)
    EMBEDDING_CHUNK_SIZE: int = Field(default=25)

    # RAG 博客检索参数
    RAG_BLOG_TOP_K: int = Field(default=3)

    # 联网搜索参数
    IQS_NUM_RESULTS: int = Field(default=10)

    # 前端路由配置（供后端生成跳转链接）
    FRONTEND_BLOG_DETAIL_PATH: str = Field(default="/blog/{slug}")

    APP_NAME: str = Field(default="DE Hub")
    APP_VERSION: str = Field(default="0.0.1")
    APP_DESCRIPTION: str = Field(default="A personal platform for DE")
    DEBUG: bool = Field(default=False)

    IQS_ENDPOINT: str = Field(default="")
    IQS_TIMEOUT: int = Field(default=45)
    IQS_API_KEY: str = Field(default="")

    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")
    REDIS_CHECKPOINT_TTL: int = Field(default=600)

    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="dehub")

    OSS_ACCESS_KEY_ID: str = Field(default="")
    OSS_ACCESS_KEY_SECRET: str = Field(default="")
    OSS_ENDPOINT: str = Field(default="")
    OSS_BUCKET_NAME: str = Field(default="")
    OSS_DOMAIN: str = Field(default="")
    OSS_USERS_AVATAR_DIR: str = Field(default="users/avatar")
    MAX_USER_AVATAR_SIZE: int = Field(default=2097152)

    OSS_BLOG_COVER_DIR: str = Field(default="blog/covers")
    MAX_BLOG_COVER_SIZE: int = Field(default=5242880)

    OSS_UPLOADS_IMAGE_DIR: str = Field(default="uploads/images")
    MAX_UPLOAD_IMAGE_SIZE: int = Field(default=5242880)

    # RAG 向量检索相似度阈值（低于此值的结果不会注入 AI 上下文）
    RAG_MIN_SIMILARITY: float = Field(default=0.6)

    @property
    def EMBEDDING_DIMENSION_EFFECTIVE(self) -> int:
        """返回生效的向量维度（若未配置则使用默认值 1024）。"""
        return self.EMBEDDING_DIMENSION or 1024

    @property
    def DATABASE_URL(self) -> str:
        """拼接 PostgreSQL 连接字符串，密码经过 URL 编码。"""
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

