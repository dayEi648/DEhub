# Plan：Agent 架构深化 — 从 create_agent 黑盒迁移到显式 StateGraph 多节点编排

## 1. 目标

将当前基于 `create_agent` 的隐式 ReAct Agent 迁移为基于显式 `StateGraph` 的多节点编排图，同时**完全保留外部 API 行为、工具生态、并发策略和 Prompt 逻辑**。

## 2. 范围边界（明确不做什么）

- **不扩展功能**：不新增工具、不新增 AI 能力、不修改 Prompt 内容
- **不改变业务行为**：前端感知不到任何变化；API 请求/响应格式完全一致
- **不引入多 Agent 协作**：本次仍为单 Agent，但内部流转显式化
- **不引入流式输出**：`ainvoke` 的阻塞式调用方式保持不变

## 3. 当前架构问题

| 问题 | 说明 |
|------|------|
| `create_agent` 是黑盒 | 对话流程（Prompt 组装 → LLM 调用 → 工具执行 → 循环）被封装在 `langchain.agents.create_agent` 内部，无法插入自定义节点 |
| 中间件与 LangGraph 两层皮 | `PromptAssemblyMiddleware` 和 `ConcurrencyMiddleware` 挂在 LangChain `AgentMiddleware` 上，而非 LangGraph 原生节点/边 |
| 按权限缓存多个 Graph 实例 | `create_agent` 要求编译时确定工具列表，导致不同权限等级缓存不同 Graph 实例，冗余且难以扩展 |
| 缺乏节点级可观测性 | 无法对"Prompt 组装耗时"、"工具选择耗时"、"工具执行耗时"做独立埋点 |

## 4. 目标架构设计

### 4.1 状态定义（State）

`ChatState` 从 `AgentState` 改为继承 `MessagesState`：

```python
from langgraph.graph import MessagesState

class ChatState(MessagesState):
    user_id: int | None = None
    conversation_id: int | None = None
    profile_text: str | None = None
    prompt_scene: str | None = None
    current_goal: str | None = None
    permission_level: int | None = None
```

- `messages` 字段使用 `add_messages` reducer，与原 `AgentState` 行为一致
- 非消息字段无 reducer，更新时直接覆盖（与原行为一致）
- `RemoveMessage(id=REMOVE_ALL_MESSAGES)` 在 `MessagesState` 中仍然有效

### 4.2 节点（Nodes）

| 节点名 | 职责 | 对应原逻辑 |
|--------|------|-----------|
| `prompt_assemble` | 过滤旧 SystemMessage，动态组装 System Prompt 并注入消息列表 | `PromptAssemblyMiddleware.wrap_model_call` |
| `agent` | 根据 `state["permission_level"]` 动态解析可见工具，绑定后调用 LLM | `create_agent` 内部的 LLM 调用逻辑 |
| `tool_executor` | 解析 AIMessage 中的 tool_calls，按并发安全策略调度执行 | `ToolNode` + `ConcurrencyMiddleware.awrap_tool_call` |
| `response_finalize` | 后处理占位节点，当前透传（预留：内容过滤、引用溯源检查等） | 无（新增占位） |

### 4.3 边（Edges）与流转

```
START ──► prompt_assemble ──► agent
                                    │
                                    ▼
                          ┌─────────────────┐
                          │  route_after_agent │
                          │   (conditional)   │
                          └─────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │ 有 tool_calls              │ 无 tool_calls
                    ▼                              ▼
            tool_executor ──► prompt_assemble   response_finalize ──► END
                     │            ▲
                     └────────────┘ (ReAct 循环)
```

- **`route_after_agent`**：检查最后一条消息是否为 `AIMessage` 且包含 `tool_calls`
  - 有 → 路由到 `tool_executor`，执行后回到 `prompt_assemble` 继续下一轮
  - 无 → 路由到 `response_finalize` → `END`

### 4.4 关键技术决策

#### 决策 1：动态工具绑定 vs 预编译缓存
- **原架构**：按 `permission_level` 预编译多个 Graph 实例缓存
- **新架构**：**单一全局 Graph 实例**，`agent` 节点内部根据 `state["permission_level"]` 动态调用 `registry.resolve()` 并 `bind_tools()`
- **理由**：`bind_tools` 开销极小（仅构造 JSON schema），简化了缓存逻辑；显式节点天然支持从 state 读取运行时参数

#### 决策 2：Prompt 组装放在独立节点
- `prompt_assemble` 作为独立节点，而非 `agent` 节点内部的一个函数调用
- **理由**：ReAct 循环中每次回到 LLM 前都需要重新组装 Prompt（因为工具结果返回后场景可能变化），独立节点使 Prompt 更新行为完全可见、可测试、可独立计时

#### 决策 3：并发控制内聚到 tool_executor 节点
- 在 `tool_executor` 节点中，按 `tool_registry` 的 `concurrency_safe` 元数据判断调度策略
- **安全工具**：同一轮内的多个 tool_calls 用 `asyncio.gather` **并行**执行
- **非安全工具**：使用 `asyncio.Lock`（模块级单例字典）按**工具名**串行执行
- **混合场景**：若一轮中同时包含安全和非安全工具，先并行执行安全组，再串行执行非安全组
- **理由**：精确复现 `ConcurrencyMiddleware` 的行为，同时消除对 LangChain Middleware 钩子的依赖

#### 决策 4：状态兼容性兜底
- 旧 Checkpoint 若因状态结构差异无法加载，`aget_state` 会返回 `None`
- `ChatService` 现有逻辑已覆盖此场景：Checkpoint 为 `None` 时自动从数据库恢复对话历史

## 5. 文件变更清单

### 5.1 修改文件

| 文件 | 变更内容 |
|------|---------|
| `backend/app/graphs/states/chat_state.py` | 基类从 `AgentState` 改为 `MessagesState`；保留所有自定义字段 |
| `backend/app/graphs/builders/chat_builder.py` | **完全重写**：移除 `create_agent`，改为显式 `StateGraph` 构建；移除按权限的多实例缓存，改为全局单例 |
| `backend/app/graphs/middleware.py` | **删除**：Prompt 组装和并发控制逻辑已迁移到独立节点 |
| `backend/app/services/chat_service.py` | 调整 `ChatService.__init__` 中 `self.graph = get_chat_graph(permission_level=...)` → `self.graph = get_chat_graph()`；其余调用点（`ainvoke`/`aget_state`/`aupdate_state`）保持不变 |

### 5.2 新增文件

| 文件 | 说明 |
|------|------|
| `backend/app/graphs/nodes/chat/__init__.py` | 节点包初始化，导出所有节点函数和路由函数 |
| `backend/app/graphs/nodes/chat/prompt_assemble.py` | Prompt 组装节点：过滤旧 SystemMessage，调用 `render_chat_system_prompt`，注入动态上下文 |
| `backend/app/graphs/nodes/chat/agent.py` | Agent 节点：从 state 读取 `permission_level`，调用 `registry.resolve()`，绑定工具，调用 LLM |
| `backend/app/graphs/nodes/chat/tool_executor.py` | 工具执行节点：解析 tool_calls，按并发策略调度，返回 ToolMessages |
| `backend/app/graphs/nodes/chat/response_finalize.py` | 后处理节点：当前透传，预留扩展接口 |
| `backend/app/graphs/nodes/chat/router.py` | 条件路由函数：`route_after_agent` |

## 6. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Checkpoint 格式不兼容 | 旧对话状态丢失 | `messages` reducer 行为一致；若加载失败，`ChatService` 自动降级为数据库恢复 |
| 锁对象生命周期变化 | 非安全工具被意外并发 | `asyncio.Lock` 字典提升至**模块级单例**，不因 Graph 重新编译而重置；测试覆盖多轮工具调用 |
| `aupdate_state` payload 行为差异 | 状态恢复/回滚/压缩失效 | 保持 `ChatState` 字段名完全一致；迁移后专项测试 `_restore_state_from_db`、`_rollback_checkpoint_state`、`_apply_compact_summary` |
| 节点异常导致 Graph 中断 | 对话失败 | 异常向上抛出，由 `ChatService.chat()` 的已有 try/except + 回滚逻辑捕获 |
| 性能回退 | `bind_tools` 每次调用都执行 | 实测开销通常在 1ms 以内，可忽略；若后续发现瓶颈，可缓存 `model.bind_tools(tools)` 结果 |

## 7. 验证策略

### 7.1 单元测试（新增）

`backend/tests/graphs/test_chat_graph.py`：

- **`test_prompt_assemble_node`**：验证旧 SystemMessage 被过滤、新 SystemMessage 被注入、动态字段（profile、goal）正确拼接
- **`test_agent_node_tool_binding`**：验证 `permission_level=0` 时只绑定公共工具，`permission_level=1` 时额外绑定管理员工具
- **`test_tool_executor_concurrency`**：模拟一轮包含 2 个安全工具 + 1 个非安全工具的 tool_calls，验证安全工具并行、非安全工具串行
- **`test_route_after_agent_with_tools`**：验证 `AIMessage` 含 `tool_calls` 时路由到 `tool_executor`
- **`test_route_after_agent_without_tools`**：验证 `AIMessage` 不含 `tool_calls` 时路由到 `END`

### 7.2 集成测试（回归）

跑通现有测试集：
- `backend/tests/test_integration_*.py`
- `backend/tests/test_*chat*.py`（若有）

### 7.3 端到端手动回归 Checklist

| 场景 | 预期 |
|------|------|
| 新建对话 → 发送"你好" | AI 正常闲聊回复，对话标题自动生成 |
| 发送"你写过 Docker 相关的博客吗" | AI 调用 `search_blog`，返回博客结果，结合结果回复 |
| 发送"今天有什么 AI 新闻" | AI 调用 `search_web`，返回搜索结果，结合结果回复 |
| 管理员发送"用户登录接口怎么调" | AI 调用 `search_openapi_docs`，返回接口信息 |
| 连续对话 20+ 轮 | 触发上下文压缩，压缩后对话继续连贯 |
| 删除对话 | 数据库记录和 Redis Checkpoint 均清理 |
| 并发请求同一对话 | 第二个请求返回 409 冲突 |

### 7.4 前端测试

- 跑通 `frontend/src/pages/AIChatPage.test.tsx`

## 8. 回滚策略

- 所有变更在独立 Git 分支中进行
- 迁移期间保留原 `chat_builder.py` 和 `middleware.py` 的备份（重命名为 `.legacy` 或注释保留）
- 若线上发现问题，回滚只需恢复 3 个文件 + 删除新增节点目录，10 分钟内完成

## 9. 实施步骤（Step → Verify）

| 步骤 | 动作 | 验证点 |
|------|------|--------|
| Step 1 | 修改 `chat_state.py`：基类改为 `MessagesState` | `ChatState` 能正常实例化，`messages` reducer 行为正确 |
| Step 2 | 新建节点文件：`prompt_assemble.py`, `agent.py`, `tool_executor.py`, `response_finalize.py`, `router.py` | 各节点函数独立测试通过 |
| Step 3 | 重写 `chat_builder.py`：组装 StateGraph，编译为全局单例 | Graph 能正常编译，`get_chat_graph()` 返回 `CompiledStateGraph` |
| Step 4 | 删除 `middleware.py`；调整 `chat_service.py` 的 Graph 获取方式 | 后端能正常启动，无导入错误 |
| Step 5 | 运行后端单元测试 + 集成测试 | 全部通过 |
| Step 6 | 运行前端测试 + 手动端到端回归 | AI 对话所有场景正常 |
| Step 7 | 清理备份文件，合入主干 | — |
