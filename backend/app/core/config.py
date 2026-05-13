from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    全局配置类，自动从 ``.env`` 文件加载环境变量。

    提供数据库连接字符串等便捷属性，所有字段均可在环境变量中覆盖。
    """
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra = "ignore",
    )
    
    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 30)

    LLM_MAIN_API_KEY: str = Field(default="")
    LLM_MAIN_BASE_URL: str = Field(default="")
    LLM_MAIN_MODEL: str = Field(default="")
    LLM_MAIN_MAX_TOKENS: int = Field(default=200000)
    LLM_MAIN_TEMPERATURE: float = Field(default=0.6)
    LLM_MAIN_TIMEOUT: int = Field(default=60)
    LLM_SMALL_API_KEY: str = Field(default="")
    LLM_SMALL_BASE_URL: str = Field(default="")
    LLM_SMALL_MODEL: str = Field(default="")
    LLM_SMALL_MAX_TOKENS: int = Field(default=100000)
    LLM_SMALL_TEMPERATURE: float = Field(default=0.6)
    LLM_SMALL_TIMEOUT: int = Field(default=60)

    EMBEDDING_API_KEY: str = Field(default="")
    EMBEDDING_BASE_URL: str = Field(default="")
    EMBEDDING_MODEL: str = Field(default="")
    EMBEDDING_DIMENSION: int | None = Field(default=None)
    EMBEDDING_TIMEOUT: int = Field(default=60)

    APP_NAME: str = Field(default="DE Hub")
    APP_VERSION: str = Field(default="0.0.1")
    APP_DESCRIPTION: str = Field(default="A personal platform for DE")
    DEBUG: bool = Field(default=False)

    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str = Field(default="")
    REDIS_SESSION_TTL: int = Field(default=1800)
    REDIS_CHAT_HISTORY_TTL: int = Field(default=1800)
    REDIS_CHAT_MAX_CONTENT: int = Field(default=20)

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

    @property
    def DATABASE_URL(self) -> str:
        """拼接 PostgreSQL 连接字符串。"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

