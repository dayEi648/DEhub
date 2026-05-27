# DEhub 博客后端 Dockerfile
# 技术栈：Python 3.12 + FastAPI + SQLAlchemy + pgvector

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖（gcc 用于编译 psycopg2-binary 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装（利用 Docker 缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 暴露端口
EXPOSE 8000

# 生产环境启动（不使用 reload）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
