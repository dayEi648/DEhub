from urllib.parse import quote_plus
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    全局配置类，自动从 ``.env`` 文件加载环境变量。

    提供数据库连接字符串等便捷属性，所有字段均可在环境变量中覆盖。
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7)

    LLM_MAIN_API_KEY: str = Field(default="")
    LLM_MAIN_BASE_URL: str = Field(default="")
    LLM_MAIN_MODEL: str = Field(default="")
    LLM_MAIN_MAX_TOKENS: int = Field(default=50000)
    LLM_MAIN_TEMPERATURE: float = Field(default=0.6)
    LLM_MAIN_TIMEOUT: int = Field(default=60)
    LLM_SMALL_API_KEY: str = Field(default="")
    LLM_SMALL_BASE_URL: str = Field(default="")
    LLM_SMALL_MODEL: str = Field(default="")
    LLM_SMALL_MAX_TOKENS: int = Field(default=50000)
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
    # 多查询检索配置
    RAG_QUERY_EXPANSION_ENABLED: bool = Field(default=True)
    RAG_QUERY_EXPANSION_COUNT: int = Field(default=5)
    RAG_QUERY_EXPANSION_TIMEOUT: int = Field(default=15)
    RAG_MULTI_QUERY_TOP_K_PER_QUERY: int = Field(default=5)

    # RAG OpenAPI 工具参数
    RAG_OPENAPI_SEARCH_TOP_K: int = Field(default=5)
    RAG_OPENAPI_CODEGEN_TOP_K: int = Field(default=3)

    # 联网搜索参数
    IQS_NUM_RESULTS: int = Field(default=10)
    IQS_NUM_RESULTS_PER_QUERY: int = Field(default=5)
    WEB_SEARCH_QUERY_EXPANSION_TIMEOUT: int = Field(default=10)

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

    # 通用缓存配置
    CACHE_ENABLED: bool = Field(default=True)
    CACHE_DEFAULT_TTL: int = Field(default=60)
    CACHE_BLOG_LIST_TTL: int = Field(default=60)
    CACHE_BLOG_HOME_TTL: int = Field(default=120)
    CACHE_BLOG_CATEGORY_TTL: int = Field(default=300)
    CACHE_BLOG_DETAIL_TTL: int = Field(default=300)
    CACHE_FORUM_ZONE_TTL: int = Field(default=300)
    CACHE_FORUM_POST_LIST_TTL: int = Field(default=60)
    CACHE_FORUM_HOT_POST_TTL: int = Field(default=90)
    CACHE_FORUM_POST_DETAIL_TTL: int = Field(default=180)

    # 浏览量计数器回写周期（秒）
    VIEW_COUNTER_FLUSH_INTERVAL_SECONDS: int = Field(default=180)

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
    # OSS 图片上传统一限制（5MB）
    MAX_OSS_IMAGE_SIZE: int = Field(default=5 * 1024 * 1024)

    OSS_USERS_AVATAR_DIR: str = Field(default="users/avatar")

    OSS_BLOG_COVER_DIR: str = Field(default="blog/covers")

    OSS_UPLOADS_IMAGE_DIR: str = Field(default="uploads/images")

    # 预留场景路径
    OSS_FORUM_POST_IMAGE_DIR: str = Field(default="forum/posts")
    OSS_FORUM_REPLY_IMAGE_DIR: str = Field(default="forum/replies")
    OSS_COMMENT_IMAGE_DIR: str = Field(default="comments/images")
    OSS_CHAT_IMAGE_DIR: str = Field(default="chat/images")

    # RAG 向量检索相似度阈值（低于此值的结果不会注入 AI 上下文）
    RAG_MIN_SIMILARITY: float = Field(default=0.6)

    # ---------- AI 对话配置 ----------
    AI_CHAT_CONTEXT_WINDOW_TOKENS: int = Field(default=1_000_000)
    AI_CHAT_COMPACT_THRESHOLD_RATIO: float = Field(default=0.85)
    AI_CHAT_COMPACT_SUMMARY_MAX_CHARS: int = Field(default=5000)
    AI_CHAT_COMPACT_LOCK_TTL_SECONDS: int = Field(default=300)
    AI_CHAT_TITLE_REGENERATE_THRESHOLD_SECONDS: int = Field(default=300)
    AI_CHAT_TITLE_MAX_LENGTH: int = Field(default=20)
    AI_CHAT_PROFILE_UPDATE_INTERVAL: int = Field(default=3)
    AI_CHAT_GOAL_TRANSCRIPT_LINES_LIMIT: int = Field(default=12)
    AI_CHAT_GOAL_GENERATION_CHAR_THRESHOLD: int = Field(default=200)

    # ---------- Agent 质量评估配置 ----------
    AI_CHAT_EVAL_ENABLED: bool = Field(default=True)
    AI_CHAT_EVAL_SAMPLE_RATE: float = Field(default=1.0)  # 0.0~1.0，1.0=全部评估

    # OpenAPI 文档上传限制（字节）
    OPENAPI_UPLOAD_MAX_SIZE: int = Field(default=10 * 1024 * 1024)

    # ---------- 博客文章配置 ----------
    # 生成摘要的正文字数阈值（去除 Markdown 标记后的有效字符数）
    BLOG_SUMMARY_CONTENT_THRESHOLD: int = Field(default=2000)
    # 摘要字数范围
    BLOG_SUMMARY_MIN_LENGTH: int = Field(default=500)
    BLOG_SUMMARY_MAX_LENGTH: int = Field(default=2000)
    # 摘要生成 LLM 超时（秒）
    BLOG_SUMMARY_LLM_TIMEOUT: int = Field(default=180)
    # 博客向量文本最大长度（超过则截断到句子边界）
    BLOG_EMBEDDING_MAX_TEXT_LENGTH: int = Field(default=6000)

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
