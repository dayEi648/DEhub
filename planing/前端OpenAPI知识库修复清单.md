# 前端 OpenAPI 知识库修复清单

> 审查日期：2026-05-27
> 审查范围：`frontend/src/types/openapiKnowledge.ts`、`api/openapiKnowledge.ts`、
> `pages/admin/OpenAPIKnowledgePage.tsx`、`pages/admin/AdminDashboard.tsx`、
> `components/Sidebar.tsx`、`pages/AIChatPage.tsx`、`index.css` 及测试文件

---

## 严重问题（功能缺陷，必须修复）

### 1. `api/openapiKnowledge.ts` — 手动设置 `Content-Type: multipart/form-data` 导致上传失败

**位置**：`frontend/src/api/openapiKnowledge.ts:17-19`

**问题代码**：
```tsx
return request.post<OpenAPIDocumentUploadResponse>(
  '/openapi_knowledge/documents/upload',
  formData,
  {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }
)
```

**原因分析**：
axios 在发送 `FormData` 时，若请求配置中**显式设置了 `Content-Type`**，则不会自动追加 `boundary` 参数。后端依赖 boundary 解析 multipart 数据，缺失 boundary 会导致文件解析失败，上传接口返回 400 或解析异常。

**修复方案**：删除手动设置的 `headers`，让 axios 自动检测 `FormData` 并生成带 boundary 的完整 `Content-Type`。

**修复后代码**：
```tsx
export async function uploadOpenAPIDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<OpenAPIDocumentUploadResponse>(
    '/openapi_knowledge/documents/upload',
    formData
  )
}
```

**验证方式**：使用浏览器 DevTools Network 面板检查上传请求的 `Content-Type` 头，确认包含 `boundary=----...`。

---

## 中等问题（与计划/规范不符，建议修复）

### 2. `OpenAPIKnowledgePage.tsx` — `formatDateTime` 未复用项目现有工具函数

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:53-57`

**问题代码**：
```tsx
function formatDateTime(raw: string) {
  const d = new Date(raw)
  if (Number.isNaN(d.getTime())) return raw
  return d.toLocaleString()
}
```

**原因分析**：
项目已在 `utils/format.ts` 中定义了标准的 `formatDateTime`（格式：`YYYY.MM.DD HH:mm`）。页面内重新定义的版本使用 `toLocaleString()`，格式随用户系统 locale 变化，导致不同页面日期格式不一致，破坏视觉统一性。

**修复方案**：删除本地定义，从 `utils/format` 导入。

**修复后代码**：
```tsx
// 删除本地 formatDateTime 定义
import { formatDateTime } from '../../utils/format'
```

---

### 3. `parseErrorMessage` 在 `AIChatPage.tsx` 和 `OpenAPIKnowledgePage.tsx` 中重复定义

**位置**：
- `frontend/src/pages/AIChatPage.tsx:19-29`
- `frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:28-38`

**原因分析**：
两个文件中定义了完全相同的 `parseErrorMessage` 函数。整合计划要求"重复代码尽量提取为共用"。当前做法增加了维护成本，若后端错误响应格式变更，需要修改两处。

**修复方案**：提取到共用工具模块，两处导入使用。

**修复步骤**：
1. 新建 `frontend/src/utils/error.ts`：
```ts
import { isAxiosError } from 'axios'

export function parseErrorMessage(
  error: unknown,
  fallback = '操作失败，请稍后重试'
): string {
  if (!isAxiosError(error)) return fallback
  const data = error.response?.data
  if (data && typeof data === 'object' && 'message' in data) {
    const maybeMessage = data.message
    if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
      return maybeMessage
    }
  }
  return fallback
}
```
2. 在 `AIChatPage.tsx` 和 `OpenAPIKnowledgePage.tsx` 中：
```tsx
import { parseErrorMessage } from '../../utils/error'
// 删除本地 parseErrorMessage 定义
```

---

### 4. 文档列表表格缺少"创建时间"列

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:459-528`

**问题分析**：
整合计划 7.3 明确要求每行展示"文件名、状态、端点数、分片数、失败原因摘要、**创建时间**、更新时间"。当前表格列：ID、文件名、状态、端点/分片、**更新时间**、操作，缺少"创建时间"。

**修复方案**：在表头和数据行各增加一列"创建时间"。

**修复后表头**：
```tsx
<tr>
  <th>ID</th>
  <th>文件名</th>
  <th>状态</th>
  <th>端点/分片</th>
  <th>创建时间</th>
  <th>更新时间</th>
  <th>操作</th>
</tr>
```

**修复后数据行**（在 `<td>{formatDateTime(doc.updated_at)}</td>` 前插入）：
```tsx
<td>{formatDateTime(doc.created_at)}</td>
```

**注意**：需同步修改空态行的 `colSpan={6}` 为 `colSpan={7}`。

---

### 5. 端点列表表格缺少"Operation ID"列

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:588-648`

**问题分析**：
整合计划 7.4 明确要求端点列表展示 "`method`、`path`、`summary`、`tags`、**`operation_id`**"。当前表格列：方法、路径、摘要、标签、操作，缺少 `operation_id`。

**修复方案**：在表头和数据行各增加一列"Operation ID"。

**修复后表头**：
```tsx
<tr>
  <th>方法</th>
  <th>路径</th>
  <th>摘要</th>
  <th>标签</th>
  <th>Operation ID</th>
  <th>操作</th>
</tr>
```

**修复后数据行**（在 `<td>{endpoint.tags?.join(', ') || '-'}</td>` 后插入）：
```tsx
<td>{endpoint.operation_id || '-'}</td>
```

**注意**：需同步修改空态行的 `colSpan={5}` 为 `colSpan={6}`。

---

### 6. 删除文档时未按 404 已删除处理

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:279-302`

**问题代码**：
```tsx
try {
  await deleteOpenAPIDocument(doc.id)
  toast.success('文档已删除')
  // ... 刷新列表
} catch (error) {
  toast.error(parseErrorMessage(error, '删除文档失败'))
}
```

**原因分析**：
整合计划 7.3 明确要求"如果删除接口返回 404，前端按已删除处理并刷新列表"。当前代码对所有异常统一显示错误 toast，若文档已被其他管理员删除或后端已清理，前端会误报删除失败，且列表残留已不存在的记录。

**修复方案**：在 catch 中区分 404 与其他错误。

**修复后代码**：
```tsx
try {
  await deleteOpenAPIDocument(doc.id)
  toast.success('文档已删除')
  if (pollingDocumentId === doc.id) {
    stopPolling()
  }
  await Promise.all([fetchDocuments(), fetchEndpoints()])
  setSearchResults([])
  setHasSearched(false)
} catch (error) {
  if (isAxiosError(error) && error.response?.status === 404) {
    toast.success('文档已删除')
    if (pollingDocumentId === doc.id) {
      stopPolling()
    }
    await Promise.all([fetchDocuments(), fetchEndpoints()])
    setSearchResults([])
    setHasSearched(false)
  } else {
    toast.error(parseErrorMessage(error, '删除文档失败'))
  }
} finally {
  setDeletingDocumentIds((prev) => prev.filter((id) => id !== doc.id))
}
```

---

## 轻微问题（代码质量/优化建议）

### 7. `fetchDocuments` 中 `overrides.status` 为 `''` 时逻辑异常

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:129-130`

**问题代码**：
```tsx
const status = overrides?.status ?? documentStatusFilter
```

**原因分析**：
JavaScript 的 `??`（空值合并运算符）将空字符串 `''` 视为 falsy，因此当显式传入 `overrides.status = ''`（意图重置为全部状态）时，表达式会返回 `documentStatusFilter`，导致重置失效。

**当前影响**：代码中未出现 `fetchDocuments({ status: '' })` 的调用，此 bug 当前未被触发，但属于潜在风险。

**修复方案**：
```tsx
const status = overrides?.status !== undefined ? overrides.status : documentStatusFilter
```

---

### 8. 上传成功后可能发起两次 `fetchDocuments` 请求

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx:260-271`

**问题代码**：
```tsx
setDocumentSkip(0)
await fetchDocuments({ skip: 0 })
```

**原因分析**：
`setDocumentSkip(0)` 触发 state 变更，在下一次渲染中 `fetchDocuments` 的 useEffect 依赖随之变化，会再次自动调用 `fetchDocuments()`。造成两次并发请求。

**当前影响**：因 `requestId` 机制存在，旧响应会被丢弃，不会导致状态错乱。但造成了不必要的网络请求。

**修复方案**（二选一）：

**方案 A**（推荐）：移除显式调用，仅依赖 useEffect 自动触发。适合 `documentSkip` 原来不为 0 的场景：
```tsx
// handleUpload 中
setDocumentSkip(0)
// 删除 await fetchDocuments({ skip: 0 })
pollDocumentStatus(res.data.document_id)
```

**方案 B**（兼容性强）：保持显式调用，确保列表一定刷新，接受 useEffect 可能带来的额外请求：
```tsx
await fetchDocuments({ skip: 0 })
setDocumentSkip(0)
pollDocumentStatus(res.data.document_id)
```

---

### 9. 移动端未实现 Tab 切换

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.tsx` 整体布局

**问题分析**：
整合计划 4.3 建议移动端改为 "文档、端点、检索" 三个 Tab 切换，当前实现为上下堆叠布局，移动端页面较长。

**修复建议**：后续迭代中增加移动端 Tab 切换组件，当前版本可接受。

---

### 10. HTTP Method Badge 未按方法区分颜色

**位置**：`frontend/src/index.css:849-859`

**问题分析**：
整合计划 7.4 建议 "HTTP 方法使用颜色 badge，但不引入过度花哨样式"。当前所有 method（GET/POST/DELETE 等）使用相同的深色背景。

**修复建议**：可为不同方法添加轻微颜色区分，例如：
- `GET` → 蓝绿色系
- `POST`/`PUT`/`PATCH` → 琥珀色系
- `DELETE` → 红色系
保持低饱和度，与现有设计体系协调。

---

### 11. 测试文件中 mock 数据不完整

**位置**：`frontend/src/pages/admin/OpenAPIKnowledgePage.test.tsx`

**问题分析**：
部分 mock 返回的数据缺少 TypeScript 类型中声明的字段，例如：
- `getOpenAPIDocumentMock` 缺少 `created_at`、`error_message`
- `uploadOpenAPIDocumentMock` 缺少 `filename`、`status`
- `searchOpenAPIKnowledgeMock` 缺少 `document_id`、`tags`、`operation_id`

**当前影响**：TypeScript 编译时不会报错（vitest mock 绕过类型检查），运行时不会导致功能错误。

**修复建议**：补全 mock 数据中的字段，使测试数据与类型定义保持一致，提升测试的可维护性和可信度。

---

## 修复优先级建议

| 优先级 | 问题编号 | 说明 |
|--------|---------|------|
| P0 | 1 | 上传功能直接不可用，必须立即修复 |
| P1 | 4, 5 | 与整合计划明确要求不符，影响验收 |
| P1 | 6 | 404 场景下用户体验异常，影响验收 |
| P2 | 2, 3 | 代码复用和一致性，建议随本次一起修复 |
| P3 | 7, 8, 11 | 代码质量，可后续逐步优化 |
| P4 | 9, 10 | 体验优化，可作为后续增强项 |

---

## 实现良好的部分（无需修改）

以下方面经检查确认符合规范，无需修改：

1. **权限控制**：`AuthGuard requireAdmin` + 页面内 `isAdmin` 判断 + `AIChatPage` 条件渲染，三层防护完整
2. **并发控制**：上传/删除 loading 锁、轮询 `pollRequestRef` 单例、`requestId` 丢弃旧响应
3. **轮询策略**：2 秒间隔、5 分钟超时、`AbortController` 取消、组件卸载清理
4. **状态反馈**：loading、disabled、空态、错误态、轮询提示均有 UI
5. **类型安全**：前端类型与接口文档一致，不含 `embedding`、`content_hash` 等内部字段
6. **数据安全**：未将 OpenAPI 内容持久化到 localStorage，错误提示不泄露文件内容
7. **回归保护**：`AIChatPage` 仅增加入口按钮，不修改对话发送、历史加载、隐藏消息开关等既有逻辑
8. **CSS 一致性**：所有新增样式复用现有 CSS 变量，无风格冲突
9. **路由挂载**：`/admin/openapi-knowledge` 正确挂载在 `/admin/*` 下，由 `AdminLayout` 统一承载
10. **测试覆盖**：权限可见性、空列表、上传后刷新、轮询不并发等关键场景已覆盖
