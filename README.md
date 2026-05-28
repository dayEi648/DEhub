# DEhub — 个人博客与创意应用平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React 19">
  <img src="https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/Vue_3-4FC08D?logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/Spring_Boot-3.5-6DB33F?logo=spring-boot&logoColor=white" alt="Spring Boot">
  <img src="https://img.shields.io/badge/LangGraph-1.2-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

这是一个以**个人博客平台**为主体，集成**智能深度研究助手**与**音乐播放与分享平台**的多应用 mono-repo 项目。三个子系统共享 PostgreSQL、Redis 等基础设施，通过 Nginx 统一网关对外提供服务。

---

## 📑 目录

- [项目简介](#-项目简介)
- [技术架构](#-技术架构)
- [仓库结构](#-仓库结构)
- [快速开始](#-快速开始)
  - [本地开发](#本地开发)
  - [Docker 部署](#docker-部署)
- [子项目详情](#-子项目详情)
  - [DEhub 博客站](#dehub-博客站)
  - [智能深度研究助手](#智能深度研究助手)
  - [EchoMemory 音乐平台](#echomemory-音乐平台)
- [环境变量](#-环境变量)
- [部署指南](#-部署指南)
- [开发规范](#-开发规范)

---

## 🚀 项目简介

| 子系统 | 入口 | 核心功能 |
|--------|------|----------|
| **DEhub 博客站** | `:80` | 博客发布、作品集展示、社区论坛、AI 智能对话、用户中心 |
| **智能深度研究助手** | `:8080` | 基于 LangGraph 的深度研究 Agent、RAG 知识库检索、联网搜索、自动报告生成 |
| **EchoMemory 音乐平台** | `:8081` | 音乐播放与管理、AI 智能推荐助手、社区互动 |

---

## 🏗 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx 统一网关                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  博客前端     │  │ DeepSearch 前端   │  │ EchoMemory 前端 │ │
│  │  React 19    │  │ Vue 3             │  │ Vue 3          │ │
│  │  :80         │  │ :8080             │  │ :8081          │ │
│  └──────┬───────┘  └────────┬─────────┘  └───────┬────────┘ │
│         │                   │                    │          │
│  ┌──────▼───────┐  ┌────────▼─────────┐  ┌───────▼────────┐ │
│  │ 博客后端      │  │ DeepSearch 后端   │  │ EchoMemory Java │ │
│  │ FastAPI      │  │ FastAPI           │  │ Spring Boot    │ │
│  │ Python 3.12  │  │ LangGraph         │  │ Java 21        │ │
│  └──────┬───────┘  └──────────────────┘  └───────┬────────┘ │
│         │                                         │          │
│  ┌──────▼─────────────────────────────────────────▼────────┐ │
│  │              PostgreSQL (pgvector)                       │ │
│  │   DB: dehub  │  DB: echomusic  │  DB: echovector         │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Redis (多 DB 隔离)                           │ │
│  │   DB0=博客  │  DB1=DeepSearch  │  DB2=Echo  │  DB3=AI    │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈总览

| 层级 | 技术选型 |
|------|----------|
| **博客前端** | React 19, TypeScript, Vite, React Router |
| **博客后端** | Python 3.12, FastAPI, SQLAlchemy, Pydantic, pgvector |
| **研究助手** | Python 3.12, FastAPI, LangGraph ≥1.2, LangChain, ChromaDB |
| **音乐前端** | Vue 3, TypeScript, Vite, Element Plus, Pinia |
| **音乐后端** | Java 21, Spring Boot 3.5, MyBatis-Plus |
| **音乐 AI** | Python 3.12, FastAPI, LangGraph |
| **基础设施** | PostgreSQL 16 (pgvector), Redis 7, Nginx, OSS |

---

## 📁 仓库结构

```
DEhub/
├── backend/                    # 博客站后端 (FastAPI)
│   ├── app/
│   │   ├── api/v1/            # REST API 路由
│   │   ├── core/              # 配置、异常处理、日志
│   │   ├── crud/              # 数据库 CRUD 操作
│   │   ├── db/                # 数据库连接与模型基类
│   │   ├── graphs/            # LangGraph AI 工作流
│   │   ├── models/            # SQLAlchemy 数据模型
│   │   ├── schemas/           # Pydantic 校验模型
│   │   ├── services/          # 业务逻辑层
│   │   └── main.py            # FastAPI 应用入口
│   ├── tests/                 # 单元测试与集成测试
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # 博客站前端 (React + Vite)
│   ├── src/
│   │   ├── pages/             # 页面组件
│   │   ├── components/        # 公共组件
│   │   ├── api/               # HTTP 请求封装
│   │   ├── hooks/             # 自定义 React Hooks
│   │   └── App.tsx            # 根组件
│   ├── tests/                 # Playwright E2E 测试
│   ├── Dockerfile
│   └── package.json
│
├── DeepSearch/                 # 智能深度研究助手
│   ├── app/
│   │   ├── agents/            # LangGraph Agent 定义
│   │   ├── rag/               # RAG 向量检索
│   │   ├── routers/           # API 路由
│   │   ├── tools/             # 工具集 (搜索、OSS、MCP)
│   │   └── main.py
│   ├── frontend/DeepResearchAgent/   # Vue 3 前端
│   ├── knowledge_base/        # 本地知识库文档
│   ├── reports/               # 生成报告存储
│   └── Dockerfile
│
├── PrjMusic/                   # EchoMemory 音乐平台
│   ├── echomusic/echoparent/  # Java 后端 (Spring Boot)
│   ├── echovue/echomusic/     # Vue 3 前端
│   ├── echoai/                # Python AI 服务 (FastAPI)
│   ├── SqlsCopy/              # 数据库初始化脚本
│   └── deploy/                # 部署脚本
│
├── deploy/nginx/               # Nginx 统一网关配置
├── docker-compose.yml          # 全站 Docker Compose 编排
├── env-deploy.example          # 生产环境变量模板
└── planning/                   # 项目文档与规划
    ├── api-documentation/
    ├── sql/
    └── frontend/
```

---

## ⚡ 快速开始

### 前置要求

- **Docker** & **Docker Compose V2**
- **Node.js** ≥ 22 (前端本地开发)
- **Python** 3.12 (后端本地开发)
- **Java** 21 (音乐平台后端本地开发)

### 本地开发

#### 1. 博客站（DEhub）

```bash
# 后端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
cp .env.example .env
# 编辑 .env 填写数据库、LLM API Key 等配置
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端 (新终端)
cd frontend
npm install --registry=https://registry.npmmirror.com
cp .env.example .env.production
npm run dev
```

#### 2. 智能深度研究助手

```bash
# 后端
cd DeepSearch
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# 前端
cd DeepSearch/frontend/DeepResearchAgent
npm install --registry=https://registry.npmmirror.com
npm run dev
```

#### 3. EchoMemory 音乐平台

```bash
# Java 后端
cd PrjMusic/echomusic/echoparent
mvn spring-boot:run

# AI 服务
cd PrjMusic/echoai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
uvicorn app.main:app --reload --host 0.0.0.0 --port 8002

# 前端
cd PrjMusic/echovue/echomusic
npm install --registry=https://registry.npmmirror.com
npm run dev
```

### Docker 部署

生产环境推荐使用 Docker Compose 一键部署：

```bash
# 1. 准备环境变量
cp env-deploy.example .env.deploy
# 编辑 .env.deploy，填写所有敏感配置（数据库密码、API Key、OSS 等）

# 2. 启动全站服务
docker compose up -d --build

# 3. 首次部署需初始化音乐平台数据库
docker compose run --rm echomusic-db-init
```

访问地址：

| 服务 | 地址 |
|------|------|
| 博客站 | http://localhost/ |
| 智能深度研究助手 | http://localhost:8080/ |
| EchoMemory 音乐平台 | http://localhost:8081/ |

---

## 📦 子项目详情

### DEhub 博客站

个人博客平台，支持文章发布、作品集展示、社区论坛、AI 智能对话等功能。

**核心模块：**
- 📝 **博客系统** — 文章分类、标签、评论、收藏
- 🎨 **作品集** — 项目展示，支持外链跳转
- 💬 **社区论坛** — 分区、发帖、回帖
- 🤖 **AI 智能对话** — 基于 LangGraph 的多轮对话，支持 RAG 知识库检索
- 👤 **用户中心** — JWT 认证、头像上传、个人资料
- 🔧 **管理后台** — 用户管理、日志审计、OpenAPI 知识库维护

### 智能深度研究助手

基于 LangGraph 构建的 AI 深度研究 Agent，能够针对用户输入的研究主题，自动执行多轮搜索、信息整合与报告生成。

**核心能力：**
- 🔍 **联网搜索** — 集成阿里云 IQS 统一搜索
- 📚 **RAG 检索** — 基于 ChromaDB 的本地知识库向量检索
- 🧠 **多 Agent 协作** — LangGraph 状态机驱动的研究流程
- 📄 **报告生成** — 自动输出 Markdown 格式研究报告，支持 OSS 存储
- 🛡️ **并发限流** — Redis -based 限流，保障服务稳定

### EchoMemory 音乐平台

音乐播放与分享平台，支持歌曲与歌单管理、AI 智能推荐与社区互动。

**核心模块：**
- 🎵 **音乐播放** — 在线播放、歌单/专辑管理、播放历史
- 🔍 **发现与搜索** — 音乐发现页、关键词搜索、Banner 推荐
- 🤖 **AI 智能音乐助手** — 基于 LangGraph 的对话式推荐（情绪推荐、兴趣推荐、用户画像推荐），支持音乐搜索、加入歌单、播放控制
- 👥 **社区互动** — 评论、私信、用户主页、关注动态
- 🔐 **JWT 认证** — 独立的用户认证体系

---

## 🔐 环境变量

项目使用多级环境变量管理：

| 文件 | 用途 | 生效范围 |
|------|------|----------|
| `backend/.env` | 博客后端开发配置 | 本地开发 |
| `frontend/.env.production` | 博客前端构建变量 | 构建时 |
| `DeepSearch/.env` | DeepSearch 开发配置 | 本地开发 |
| `PrjMusic/echoai/.env` | EchoAI 开发配置 | 本地开发 |
| `.env.deploy` | **生产环境统一配置** | Docker Compose |

**关键配置项：**

- `POSTGRES_PASSWORD` — PostgreSQL 数据库密码
- `DEHUB_SECRET_KEY` / `ECHOMUSIC_JWT_SECRET` — JWT 签名密钥
- `LLM_MAIN_API_KEY` / `LLM_SMALL_API_KEY` — 大模型 API Key
- `EMBEDDING_API_KEY` — Embedding 向量模型 API Key（阿里云百炼）
- `IQS_API_KEY` / `IQSSEARCH_API_KEY` — 阿里云 IQS 搜索 API Key
- `DASHSCOPE_API_KEY` — 阿里云百炼 API Key
- `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` — DeepSearch LLM API Key
- `ECS_IP` — 服务器公网 IP（前端构建注入）
- 各子系统独立的 **OSS 配置** — 图片、报告、缩略图存储

> ⚠️ **安全提示**：所有包含敏感信息的 `.env` 文件均已加入 `.gitignore`，请勿提交到版本控制。

---

## 🚢 部署指南

### 生产环境（ECS / 云服务器）

1. **服务器准备**（Ubuntu 22.04）
   ```bash
   apt update && apt install -y docker.io docker-compose-plugin
   systemctl start docker && systemctl enable docker
   ```

2. **上传代码**
   ```bash
   # 本地打包（排除 node_modules、.venv 等）
   tar -czf dehub-deploy.tar.gz --exclude="*/node_modules" --exclude="*/.venv" --exclude="*/dist" --exclude=".git" -C . .
   
   # 上传到服务器
   scp dehub-deploy.tar.gz root@<ECS_IP>:/opt/dehub.tar.gz
   ```

3. **服务器启动**
   ```bash
   mkdir -p /opt/dehub && cd /opt/dehub
   tar -xzf /opt/dehub.tar.gz
   docker compose up -d --build
   ```

详细部署流程请参考 [`DEPLOY.md`](DEPLOY.md)。

---

## 📝 开发规范

- **语言**：所有用户界面与文档使用简体中文
- **代码风格**：遵循各技术栈官方推荐规范（PEP 8、ESLint / Prettier）
- **测试**：核心功能需覆盖单元测试与集成测试（博客前端使用 Playwright + Vitest）
- **Git 工作流**：功能分支开发，通过 Pull Request 合并至主分支
- **依赖管理**：中国大陆网络环境下，包管理器默认使用国内镜像源

更多开发规范与项目背景，请参考根目录及各子目录下的 [`AGENTS.md`](AGENTS.md) 文件。

---

<p align="center">
  由 <strong>de</strong> 构建与维护
</p>
