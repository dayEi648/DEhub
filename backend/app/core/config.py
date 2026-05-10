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
    
    APP_NAME: str = Field(default="DE Hub")
    APP_VERSION: str = Field(default="0.0.1")
    APP_DESCRIPTION: str = Field(default="A personal platform for DE")
    DEBUG: bool = Field(default=False)

    REDIS_HOST: str = Field(default="redis")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_SESSION_TTL: int = Field(default=1800)

    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="")
    POSTGRES_DB: str = Field(default="DEhub")

    @property
    def DATABASE_URL(self) -> str:
        """拼接 PostgreSQL 连接字符串。"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()

