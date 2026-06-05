# DEhub — 个人博客与创意平台

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white" alt="Python 3.12">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white" alt="React 19">
  <img src="https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/LangGraph-1.2-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL 16">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
</p>

DEhub 是开发者 **de** 的个人博客平台，集博客发布、作品集展示、社区论坛与 AI 智能对话于一体。平台以内容为核心，通过 LangGraph 驱动的 AI Agent 提供具备长记忆、RAG 知识库检索与联网搜索能力的智能对话体验。

---

## 📑 目录

- [项目简介](#-项目简介)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
  - [本地开发](#本地开发)
  - [生产部署](#生产部署)
- [AI 核心实现](#-ai-核心实现)
  - [Agent 架构设计](#agent-架构设计)
  - [RAG 向量检索](#rag-向量检索)
  - [长对话记忆](#长对话记忆)
  - [用户画像与目标感知](#用户画像与目标感知)
- [环境变量](#-环境变量)
- [开发规范](#-开发规范)

---

## 🚀 项目简介

| 模块 | 说明 |
|------|------|
| **博客系统** | 文章分类、标签、评论、收藏，支持 Markdown 编辑 |
| **作品集** | 项目展示，支持外链跳转 |
| **社区论坛** | 分区、发帖、回帖、点赞、关注 |
| **AI 智能对话** | 基于 LangGraph 的多轮对话，支持 RAG 博客检索、联网搜索、用户画像记忆 |
| **用户中心** | JWT 认证、头像上传、个人资料 |
| **管理后台** | 用户管理、日志审计、OpenAPI 知识库维护 |

---

## 🏗 技术架构

```
┌─────────────────────────────────────────────┐
│              Nginx 统一网关                   │
│         前端 (React 19 + Vite)               │
│              ↓                               │
│         后端 (FastAPI + LangGraph)           │
│              ↓                               │
│    ┌─────────┴─────────┐                    │
│    │  PostgreSQL (pgvector)                 │
│    │  Redis (缓存 / Checkpoint / 计数器)     │
│    └─────────────────────┘                  │
└─────────────────────────────────────────────┘
```

| 层级 | 技术选型 |
|------|----------|
| **前端** | React 19, TypeScript, Vite, React Router, Tailwind CSS |
| **后端** | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic, Alembic |
| **AI 框架** | LangGraph ≥1.2, LangChain, OpenAI Embedding 兼容层 |
| **数据库** | PostgreSQL 16 (pgvector), pgvector HNSW 索引 |
| **缓存** | Redis 7 (多级缓存、对话 Checkpoint、浏览量计数、分布式锁) |
| **部署** | Docker Compose, Nginx |
| **对象存储** | 阿里云 OSS |

---

## ⚡ 快速开始

### 前置要求

- **Docker** & **Docker Compose V2**（生产部署）
- **Node.js** ≥ 22（前端本地开发）
- **Python** 3.12（后端本地开发）

### 本地开发

**后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
cp .env.example .env
# 编辑 .env 填写数据库、LLM API Key 等配置
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端（新终端）**

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
cp .env.example .env.production
npm run dev
```

访问：`http://localhost:5173`

### 生产部署

```bash
# 1. 准备环境变量
cp env-deploy.example .env.deploy
# 编辑 .env.deploy，填写所有敏感配置（数据库密码、API Key、OSS 等）

# 2. 打包上传至服务器（Windows PowerShell）
tar -czf ./dehub-deploy.tar.gz `
  --exclude="backend/.venv" `
  --exclude="backend/__pycache__" `
  --exclude="frontend/node_modules" `
  --exclude="frontend/dist" `
  --exclude=".git" `
  -C . backend frontend deploy docker-compose.yml .env.deploy .gitignore

scp ./dehub-deploy.tar.gz root@<ECS_IP>:/opt/dehub.tar.gz

# 3. 服务器启动（Ubuntu）
mkdir -p /opt/dehub && cd /opt/dehub
tar -xzf /opt/dehub.tar.gz -C /opt/dehub
docker compose --env-file .env.deploy up -d --build
```

详细部署流程请参考 [`DEPLOY.md`](DEPLOY.md)。

---

## 🤖 AI 核心实现

### Agent 架构设计

AI 对话基于 **LangGraph 显式状态机编排**，从黑盒 `create_agent` 迁移为可观测、可调试的多节点图结构：

```
START → agent_node → [含 tool_calls ?] → tool_executor_node → agent_node → END
                                      [无 tool_calls] → END
```

**关键设计**

- **节点职责分离**：`agent_node` 负责 Prompt 组装、动态工具绑定与 LLM 调用；`tool_executor_node` 负责解析 tool_calls 并调度执行；`route_after_agent` 根据 AIMessage 是否含 tool_calls 决定下一跳。
- **工具治理层**：在 LangChain `@tool` 之上引入 `ToolMetadata`（风险等级、作用域、并发安全性），通过 `ToolRegistry` 按用户权限动态过滤可用工具。管理员专享 OpenAPI 知识库检索工具，普通用户无感知。
- **并发安全策略**：工具声明自身是否支持并发。安全工具（如搜索）并行执行；非安全工具（如收藏、关注）按工具名加 `asyncio.Lock` 串行执行，避免竞态条件。
- **动态 Prompt 组装**：固定部分（角色设定、安全约束、输出风格）+ 动态部分（当前时间、场景、用户画像、当前目标）。SystemMessage 仅作为 LLM 调用临时参数，不持久化到状态，减少上下文污染。

### RAG 向量检索

平台实现 **双路 RAG**，均基于 PostgreSQL pgvector + HNSW 索引：

| 知识库 | 用途 | 特点 |
|--------|------|------|
| **博客文章向量库** | 回答与 DEhub 博客内容相关的问题 | 多查询并行检索：small model 改写 query → 并发 embedding + 向量检索 → 按 post_id 去重保留最高相似度 → 全局重排序 |
| **OpenAPI 端点向量库** | 管理员查询系统内部接口 | 端点级语义检索，按 `content_hash` 去重避免重复 embedding |

**Query Expansion（查询扩展）**：用户原始 query 经 small model 改写为多条不同角度的精炼查询，显著提升召回率和精确率。改写失败时自动降级为单查询。

**相似度阈值过滤**：低于设定阈值的检索结果不会注入 AI 上下文，避免无关信息干扰。

### 长对话记忆

为解决长对话上下文窗口耗尽问题，实现 **自动上下文压缩（Context Compact）**：

- **阈值触发**：当 LLM 返回的真实 prompt_tokens（DeepSeek API usage）达到窗口容量的 85% 时触发压缩，不再依赖 tiktoken 估算。
- **摘要生成**：调用 small model 将历史对话压缩为摘要，保留关键事实、偏好、目标、约束、已达成结论。
- **保留最近一轮**：压缩时保留最新一轮用户输入与 AI 回复，确保对话连贯性。
- **双轨持久化**：摘要入库供前端展示（脱敏为「已自动压缩上下文」），同时更新 Redis Checkpoint 替换历史消息。
- **失败回滚**：Checkpoint 更新失败时回滚数据库写入，避免两条历史线分叉。

**Redis Checkpoint（自定义实现）**：

- 基于标准 Redis（无需 RedisJSON / RediSearch），仅使用 STRING + EXPIRE。
- Shallow 模式：每个 thread 只保留最新 checkpoint，支持 TTL 自动过期。
- 自定义序列化：带类型标记的二进制编码，兼容 LangGraph 的 serde 协议。

### 用户画像与目标感知

- **用户画像（Profile）**：每 3 轮用户消息自动触发 small model 判断对话中是否包含值得记录的个人信息（兴趣、偏好、技能、习惯等），若值得记录则更新画像。画像文本实时注入 system prompt，使 AI 能感知用户特征。
- **当前目标（Current Goal）**：small model 根据对话上下文提炼用户核心目标（5~200 字），注入 system prompt 引导 AI 回复聚焦，避免话题漂移。
- **对话级锁**：基于 Redis 分布式锁（Lua 脚本保证原子性），防止同一对话并发请求导致上下文混乱或重复压缩。

### 可观测性

- **Agent 行为监测**：通过 `AsyncCallbackHandler` 注入 graph 执行链路，自动捕获 graph / node / llm / tool 各级事件，构建 trace/span 树。
- **Token 级监控**：精确记录 DeepSeek API 返回的 prompt_tokens、completion_tokens、cache_hit_tokens、reasoning_tokens。
- **后台异步持久化**：监测数据通过后台任务管理器异步写入数据库，零阻塞主流程。

### 缓存与性能

- **多级缓存基础设施**：支持 JSON 序列化、标签批量失效、TTL ±10% 抖动防雪崩、Redis 异常降级。
- **浏览量计数器**：Redis 作为写缓冲区，后台协程定期批量回写数据库，消除详情页高频写操作。
- **热点 key 防击穿**：分布式锁 + 双重检查，确保缓存重建仅执行一次。

---

## 🔐 环境变量

| 文件 | 用途 |
|------|------|
| `backend/.env` | 后端开发配置 |
| `frontend/.env.production` | 前端构建变量 |
| `.env.deploy` | **生产环境统一配置** |

**关键配置项**

- `POSTGRES_PASSWORD` — PostgreSQL 密码
- `DEHUB_SECRET_KEY` — JWT 签名密钥
- `LLM_MAIN_API_KEY` / `LLM_SMALL_API_KEY` — 大/小模型 API Key
- `EMBEDDING_API_KEY` — Embedding 向量模型 API Key（阿里云百炼兼容层）
- `IQS_API_KEY` — 阿里云 IQS 统一搜索 API Key（联网搜索）
- `DEHUB_OSS_*` — 阿里云 OSS 配置

> ⚠️ 所有 `.env` 文件均已加入 `.gitignore`，请勿提交到版本控制。

---

## 📝 开发规范

- **语言**：所有用户界面与文档使用简体中文
- **代码风格**：遵循各技术栈官方推荐规范（PEP 8、ESLint / Prettier）
- **测试**：核心功能覆盖单元测试与集成测试（pytest / Playwright E2E）
- **Git 工作流**：功能分支开发，通过 Pull Request 合并
- **依赖管理**：中国大陆网络环境下，包管理器默认使用国内镜像源


---

<p align="center">
  由 <strong>de</strong> 构建与维护
</p>
