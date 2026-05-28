"""
集中配置管理，使用 pydantic-settings 从环境变量读取。
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库（敏感，强制环境变量）
    echomusic_db_url: str = Field(..., description="主数据库连接串")
    echovector_db_url: str = Field(..., description="向量库连接串")

    # Redis（敏感，强制环境变量）
    redis_url: str = Field(..., description="Redis 连接串")

    # JWT（与 Spring 一致，敏感，强制环境变量）
    jwt_secret: str = Field(..., description="JWT 签名密钥")

    # LLM（阿里云百炼）
    openai_api_key: str = ""
    openai_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    openai_model: str = "deepseek-v4-pro"
    openai_model_fast: str = "deepseek-v4-flash"

    # Embedding
    embedding_model: str = "text-embedding-v4"
    embedding_dimension: int = 1024

    # IQS 搜索
    iqs_api_key: str = ""
    iqs_endpoint: str = "https://cloud-iqs.aliyuncs.com/search/unified"

    # Spring 后端地址（AI 服务写操作时调用）
    spring_base_url: str = "http://localhost:8080"

    # 连接池
    db_pool_min_size: int = 2
    db_pool_max_size: int = 10
    db_command_timeout: int = 60


settings = Settings()
