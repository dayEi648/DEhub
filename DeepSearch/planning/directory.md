---
name: Project directory
description: This is the directory structure of the entire project, which needs to be updated frequently.
---

### 根目录
```
DeepSearch/                      # 项目根目录
├── app/                         # 后端 FastAPI 应用
│   ├── agents/                  # LangGraph Agent 节点与状态机
│   ├── routers/                 # FastAPI 路由（API 接口）
│   ├── tools/                   # 工具封装（MCP、Redis、OSS、限流）
│   ├── rag/                     # RAG 知识库（ChromaDB 向量检索）
│   ├── config.py                # 配置管理（Pydantic Settings）
│   └── main.py                  # FastAPI 应用入口
├── frontend/                    # 前端工程
│   └── DeepResearchAgent/       # Vue 3 + Vite SPA
├── knowledge_base/              # 研究方法论原始文档（Markdown）
├── reports/                     # 生成的报告本地输出目录（开发/兜底）
├── deploy/                      # 部署配置文件（Nginx、systemd、部署手册）
├── chroma_db/                   # ChromaDB 向量库本地数据
├── .env                         # 环境变量（API Key、OSS、Redis 等，不提交 Git）
├── .env.example                 # 环境变量模板
├── requirements.txt             # Python 依赖
├── mcp_settings.json            # MCP Server 配置
└── 实现文档.md / 接口文档.md / 智能深度研究助手_项目设计文档.md   # 项目文档
```

### 前端工程目录
```
frontend/DeepResearchAgent/
├── src/
│   ├── views/                   # 页面视图（SubmitView / ProgressView / ReportView）
│   ├── components/              # 可复用组件（导航、步骤条、日志面板等）
│   ├── stores/                  # Pinia 全局状态管理
│   ├── api/                     # Axios API 封装 + SSE 连接
│   ├── utils/                   # 工具函数（Markdown 渲染、目录提取）
│   └── styles/                  # 全局样式（CSS Variables、动画）
├── index.html                   # 入口 HTML
├── package.json                 # Node 依赖
└── vite.config.js               # Vite 构建配置
```

### 后端工程目录
```
app/
├── __init__.py
├── main.py                      # FastAPI 入口：CORS、健康检查、路由注册、静态文件
├── config.py                    # 配置管理：LLM Key、Redis、OSS、项目路径
├── routers/
│   ├── __init__.py
│   └── research.py              # /research 路由：任务提交、状态查询、SSE 流式
├── agents/
│   ├── __init__.py
│   ├── state.py                 # ResearchState TypedDict 定义
│   ├── nodes.py                 # 5 个 Agent 节点实现（Planner/Researcher/Analyzer/Writer/Reviewer）
│   └── graph.py                 # LangGraph 状态机构建 + save_report_node
├── tools/
│   ├── __init__.py
│   ├── mcp_client.py            # MCP 客户端（SSE 连接 IQS Search）
│   ├── search_cache.py          # Redis 搜索缓存
│   ├── rate_limiter.py          # Redis 滑动窗口限流器
│   ├── redis_checkpoint.py      # 自定义 Redis Checkpoint Saver
│   └── oss_client.py            # 阿里云 OSS 客户端封装（报告上传/下载）
└── rag/
    ├── __init__.py
    └── vectorstore.py           # ChromaDB 向量库初始化与检索
```
