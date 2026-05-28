# 智能深度研究助手后端 Dockerfile
# 技术栈：Python 3.12 + FastAPI + LangGraph + ChromaDB

FROM python:3.12-slim

WORKDIR /app

# 更换 Debian 源为国内镜像（加速 apt 下载）
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true \
    && sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装（使用国内 PyPI 镜像）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制应用代码
COPY app/ ./app/
COPY mcp_settings.json .

# 创建数据目录（用于 ChromaDB 持久化）
RUN mkdir -p /app/chroma_db /app/reports

# 暴露端口
EXPOSE 8000

# 生产环境启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
