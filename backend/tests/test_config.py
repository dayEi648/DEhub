"""配置模块单元测试。"""

from pathlib import Path

import pytest
from app.core.config import Settings


class TestEnvFilePath:
    """测试配置文件读取路径。"""

    def test_env_file_points_to_backend_env(self):
        """Settings 应固定读取 backend/.env，不依赖进程当前工作目录。"""
        env_file = Path(Settings.model_config["env_file"])
        assert env_file.name == ".env"
        assert env_file.parent.name == "backend"


class TestDatabaseUrl:
    """测试 DATABASE_URL 拼接逻辑。"""

    def test_password_with_special_chars(self):
        """密码包含特殊字符时应被正确 URL 编码。"""
        settings = Settings(
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="p@ss:w0rd/",  # 包含 @ : /
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="testdb",
        )
        url = settings.DATABASE_URL
        assert "p%40ss%3Aw0rd%2F" in url
        assert "@" not in url.split("@")[0].split(":")[-1]

    def test_password_with_empty_string(self):
        """空密码时不应引入多余的冒号。"""
        settings = Settings(
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="",
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="testdb",
        )
        url = settings.DATABASE_URL
        assert url == "postgresql://user:@localhost:5432/testdb"

    def test_password_with_plus_sign(self):
        """密码包含加号时应被编码为 %2B。"""
        settings = Settings(
            POSTGRES_USER="user",
            POSTGRES_PASSWORD="my+secret",
            POSTGRES_HOST="localhost",
            POSTGRES_PORT=5432,
            POSTGRES_DB="testdb",
        )
        url = settings.DATABASE_URL
        assert "my%2Bsecret" in url
