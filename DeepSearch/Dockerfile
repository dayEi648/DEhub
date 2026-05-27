# 智能深度研究助手后端 Dockerfile
# 技术栈：Python 3.12 + FastAPI + LangGraph + ChromaDB

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY mcp_settings.json .

# 创建数据目录（用于 ChromaDB 持久化）
RUN mkdir -p /app/chroma_db /app/reports

# 暴露端口
EXPOSE 8000

# 生产环境启动
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
