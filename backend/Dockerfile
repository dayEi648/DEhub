# DEhub 博客后端 Dockerfile
# 技术栈：Python 3.12 + FastAPI + SQLAlchemy + pgvector

FROM python:3.12-slim

WORKDIR /app

# 更换 Debian 源为国内镜像（加速 apt 下载）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖（gcc 用于编译 psycopg2-binary 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装（利用 Docker 缓存层 + BuildKit 挂载缓存，使用国内 PyPI 镜像）
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制应用代码
COPY app/ ./app/

# 复制 alembic 配置与迁移脚本（启动时自动执行数据库迁移）
COPY alembic.ini .
COPY alembic/ ./alembic/

# 暴露端口
EXPOSE 8000

# 生产环境启动（不使用 reload）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
