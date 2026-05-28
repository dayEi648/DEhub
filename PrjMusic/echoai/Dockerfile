# =============================================================================
# EchoAI — PrjMusic Python AI 服务（FastAPI + LangGraph）
# =============================================================================
# 风格与 DeepSearch Dockerfile 保持一致
# =============================================================================

FROM python:3.12-slim

WORKDIR /app

# 替换 Debian 源为阿里云镜像
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（如有需要可扩展）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 使用阿里云 PyPI 镜像，利用 BuildKit cache 加速
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/

# 复制应用代码
COPY app/ ./app/

# 创建运行时目录
RUN mkdir -p /app/chroma_db /app/reports

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
