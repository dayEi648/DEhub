---
name: Project directory
description: 当你需要了解该项目的目录结构时，查阅此文档；如果你对项目目录和文件进行了任何的变更，都需要更新该文档。
---

## backend/

```
backend/                    # 后端工程（FastAPI）
├── app/                    # 应用主目录
│   ├── api/                # API 路由与依赖注入
│   │   └── v1/             # API v1 版本路由（按模块拆分）
│   ├── core/               # 核心配置与安全工具
│   ├── crud/               # 数据库 CRUD 操作（按模块拆分）
│   ├── db/                 # 数据库连接与 ORM 基类
│   ├── graphs/             # LangGraph 状态机与工作流定义（AI 对话编排）
│   │   ├── builders/       # 图编译构建器
│   │   ├── nodes/          # 图节点定义
│   │   │   └── toolnodes/  # LangChain Tool 节点（供 LLM Tool Calling）
│   │   └── states/         # 图状态定义
│   ├── infrastructure/     # 外部基础设施客户端（LLM、Embedding、Redis、Checkpoint、Cache）
│   ├── models/             # SQLAlchemy ORM 模型（按模块拆分）
│   ├── prompts/            # AI 对话 Prompt 模板
│   ├── schemas/            # Pydantic 数据校验模型（按模块拆分）
│   ├── services/           # 业务逻辑层（按模块拆分）
│   ├── storage/            # 文件存储与本地资源管理
│   └── utils/              # 后端通用工具函数
├── tests/                  # 测试目录（含缓存基础设施与业务缓存集成测试）
├── requirements.txt        # Python 依赖清单
└── run.py                  # 应用启动入口
```

## frontend/

```
frontend/                   # 前端工程
├── src/                    # React + TypeScript 源码
│   ├── api/                # 前端 API 请求封装（含 AI 对话 aiChat.ts）
│   ├── components/         # 可复用 UI 组件（含 AppTopNav、AuthGuard、后台布局）
│   ├── pages/              # 页面组件（登录、首页、博客、论坛、AI 对话、个人中心、后台）
│   ├── types/              # 前端 TypeScript 类型定义（含 AI 对话 aiChat.ts）
│   └── utils/              # 前端通用工具（鉴权、本地存储、请求实例）
├── public/                 # Vite 静态资源目录
├── package.json            # 前端依赖与脚本
├── eslint.config.js        # ESLint 配置
├── vite.config.ts          # Vite 配置（含本地开发代理与项目根目录字体访问）
└── tsconfig*.json          # TypeScript 配置
```

## DEhub/

```
DEhub/                      # 项目根目录（前后端之外的全局文件与目录）
├── planing/                # 计划、设计与接口文档（按模块拆分为独立接口文档）
│   ├── Redis缓存开发计划.md  # 首页、博客与论坛列表 Redis 缓存策略开发计划
│   ├── 修复计划.md          # 论坛帖子列表瘦身、回复点赞计数与 Redis 缓存一致性修复计划
│   └── 前端代码检查报告.md   # 前端代码全面审查报告（问题清单与改进建议）
├── sql/                    # SQL 建表语句
├── 废弃/                    # 废弃或归档文件
├── AGENTS.md               # Agent 开发规范与项目背景
├── Redis缓存策略.md         # Redis 缓存 Key、TTL、失效策略技术文档（可选）
├── DIRECTORY.md            # 项目目录结构说明（本文件）
├── GIT.md                  # Git 操作规范
└── 技术亮点.md              # 项目技术亮点记录
```
