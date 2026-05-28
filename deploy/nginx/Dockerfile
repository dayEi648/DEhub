# 统一 nginx 镜像
# 多阶段构建：分别构建两个前端，最终由 nginx 提供静态文件服务

# ==================== Stage 1: 构建博客前端 ====================
FROM node:22-slim AS dehub-frontend-builder
ARG VITE_ECS_IP
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmmirror.com && npm install
COPY frontend/ ./
RUN echo "VITE_ECS_IP=${VITE_ECS_IP}" > .env.production
RUN npm run build

# ==================== Stage 2: 构建 DeepSearch 前端 ====================
FROM node:22-slim AS deepsearch-frontend-builder
WORKDIR /app/deepsearch-frontend
COPY DeepSearch/frontend/DeepResearchAgent/package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm config set registry https://registry.npmmirror.com && npm install
COPY DeepSearch/frontend/DeepResearchAgent/ ./
RUN npm run build

# ==================== Stage 3: nginx 运行 ====================
FROM nginx:alpine

# 复制两个前端构建产物到不同目录
COPY --from=dehub-frontend-builder /app/frontend/dist /usr/share/nginx/html/dehub
COPY --from=deepsearch-frontend-builder /app/deepsearch-frontend/dist /usr/share/nginx/html/deepsearch

# 复制 nginx 配置
COPY deploy/nginx/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80 8080

CMD ["nginx", "-g", "daemon off;"]
