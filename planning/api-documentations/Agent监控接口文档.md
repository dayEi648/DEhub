# Agent 监控接口文档

## 1. 接口概览

### 1.1 Agent 监控

| 方法 | 路径 | 功能简述 | 认证要求 |
|------|------|---------|---------|
| GET | `/api/v1/agent_monitoring/traces` | 查询 AgentTrace 列表 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/traces/{trace_id}` | 获取单条 AgentTrace 详情 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/traces/{trace_id}/spans` | 获取某 trace 下的所有 spans | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/stats` | 获取 AgentTrace 统计概览 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/evaluations` | 查询 AgentEvaluation 列表 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/evaluations/stats` | 获取评估统计概览 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/evaluations/trend` | 获取最近 N 天评估趋势 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/traces/{trace_id}/evaluations` | 获取某 trace 下的所有评估记录 | 管理员及以上 |
| POST | `/api/v1/agent_monitoring/traces/{trace_id}/evaluate` | 手动触发对指定 trace 的评估 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/traces/export` | 导出 AgentTrace 数据 | 管理员及以上 |
| GET | `/api/v1/agent_monitoring/evaluations/export` | 导出 AgentEvaluation 数据 | 管理员及以上 |

---

## 2. 枚举与常量定义

| 常量/枚举 | 值 | 说明 |
|-----------|-----|------|
| Trace 状态 `status` | `"started"` | 已开始 |
| | `"completed"` | 已完成 |
| | `"failed"` | 失败 |
| 导出格式 `format` | `"json"` | JSON 格式（默认） |
| | `"csv"` | CSV 格式 |
| 默认分页 | `skip=0, limit=20` | 列表接口默认值，`limit` 上限 `100` |
| 评估列表分页 | `skip=0, limit=50` | 评估列表默认值，`limit` 上限 `200` |
| 趋势天数 | `days=7` | 趋势接口默认值，范围 `1~30` |

---

## 3. 统一封装返回结果

### 3.1 成功返回

后端**未**对成功响应做统一封装。接口成功时，直接返回对应 Schema 序列化后的 JSON，HTTP 状态码通常为 `200`（删除操作为 `204`，导出接口返回文件流）。

### 3.2 错误返回

所有错误响应均由全局异常处理器统一封装，结构如下：

```json
{
  "code": <HTTP状态码>,
  "message": "错误描述",
  "detail?": "可选的详细错误信息"
}
```

| 场景 | HTTP 状态码 | `message` | 说明 |
|------|------------|-----------|------|
| 参数校验失败 | `422` | 请求参数校验失败 | 附 `detail: [...]` 具体字段错误 |
| 未认证 | `401` | 缺少认证令牌 / 令牌校验失败 | — |
| 权限不足 | `403` | 权限不足 | 非管理员访问 |
| Trace/端点不存在 | `404` | Trace 不存在 / 端点不存在 | — |
| 未预料异常 | `500` | 服务器内部错误 | 兜底，不暴露堆栈 |

---

## 4. 认证说明

所有接口均需在请求头中携带访问令牌：

```
Authorization: Bearer <access_token>
```

令牌失效或缺失时，返回 `401`：

```json
{
  "code": 401,
  "message": "缺少认证令牌"
}
```

**权限要求**：所有 Agent 监控接口均要求当前用户为**管理员及以上**（`permission ≥ 1`）。普通用户调用将返回 `403`。

---

## 5. 公共响应类型

### `AgentTraceResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 记录 ID |
| trace_id | string | Trace 唯一标识 |
| conversation_id | integer \| null | 关联对话 ID |
| user_id | integer \| null | 关联用户 ID |
| graph_name | string | 图名称 |
| status | string | 状态：`started` / `completed` / `failed` |
| input_message | string \| null | 输入消息 |
| output_message | string \| null | 输出消息 |
| total_tokens | integer \| null | 总 Token 数 |
| prompt_tokens | integer \| null | Prompt Token 数 |
| completion_tokens | integer \| null | Completion Token 数 |
| tool_calls_count | integer | 工具调用次数 |
| node_steps | integer | 节点步数 |
| latency_ms | integer \| null | 延迟（毫秒） |
| started_at | string(datetime) | 开始时间 |
| ended_at | string(datetime) \| null | 结束时间 |
| error_type | string \| null | 错误类型 |
| error_message | string \| null | 错误消息 |
| is_flagged | boolean | 是否被标记 |
| meta | object \| null | 元数据 |

### `AgentSpanResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 记录 ID |
| trace_id | string | 所属 Trace ID |
| parent_span_id | integer \| null | 父 Span ID |
| span_type | string | Span 类型 |
| span_name | string | Span 名称 |
| status | string | 状态 |
| started_at | string(datetime) | 开始时间 |
| ended_at | string(datetime) \| null | 结束时间 |
| latency_ms | integer \| null | 延迟（毫秒） |
| input_data | object \| null | 输入数据 |
| output_data | object \| null | 输出数据 |
| error_info | object \| null | 错误信息 |
| token_usage | object \| null | Token 使用量 |
| meta | object \| null | 元数据 |

### `AgentTraceStatsResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| total | integer | Trace 总条数 |
| today_count | integer | 今日 Trace 条数 |
| failed_count | integer | 失败 Trace 条数 |
| avg_latency_ms | integer | 平均延迟（毫秒） |

### `AgentEvaluationResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 记录 ID |
| trace_id | string | 所属 Trace ID |
| conversation_id | integer \| null | 关联对话 ID |
| eval_type | string | 评估类型 |
| dimension | string | 评估维度 |
| score | float | 评分（`0.0 ~ 1.0`） |
| reason | string \| null | 评估理由 |
| evaluated_at | string(datetime) | 评估时间 |
| evaluator_model | string \| null | 评估模型 |
| meta | object \| null | 元数据 |

### `AgentEvaluationStatsResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| total_evaluations | integer | 评估总条数 |
| avg_score | float | 平均评分 |
| low_score_count | integer | 低分条数 |
| dimension_avgs | object[] | 各维度平均分 |

### `AgentEvaluationTrendResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| items | object[] | 趋势数据项 |

---

## 6. 单接口详细定义

### 6.1 查询 AgentTrace 列表

---

### GET `/api/v1/agent_monitoring/traces`

- **功能**：查询 AgentTrace 列表（分页 + 多条件筛选）
- **认证**：管理员及以上（`permission ≥ 1`）

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `≥ 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~100`，默认 `20` | 返回数量上限 |
| conversation_id | integer | 否 | — | 按对话 ID 筛选 |
| user_id | integer | 否 | — | 按用户 ID 筛选 |
| status | string | 否 | `started`/`completed`/`failed` | 按状态筛选 |
| is_flagged | boolean | 否 | — | 按是否被标记筛选 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentTraceListResponse`

```json
{
  "items": [AgentTraceResponse],
  "total": 100
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.2 获取单条 AgentTrace 详情

---

### GET `/api/v1/agent_monitoring/traces/{trace_id}`

- **功能**：获取单条 AgentTrace 详情
- **认证**：管理员及以上（`permission ≥ 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trace_id | string | 是 | Trace 唯一标识 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentTraceResponse`

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 404 | Trace 不存在 |
| 403 | 权限不足 |

---

### 6.3 获取某 trace 下的所有 spans

---

### GET `/api/v1/agent_monitoring/traces/{trace_id}/spans`

- **功能**：获取某 trace 下的所有 spans
- **认证**：管理员及以上（`permission ≥ 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trace_id | string | 是 | Trace 唯一标识 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentSpanListResponse`

```json
{
  "items": [AgentSpanResponse]
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |

---

### 6.4 获取 AgentTrace 统计概览

---

### GET `/api/v1/agent_monitoring/stats`

- **功能**：获取 AgentTrace 统计概览（Dashboard 数据）
- **认证**：管理员及以上（`permission ≥ 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentTraceStatsResponse`

```json
{
  "total": 128,
  "today_count": 5,
  "failed_count": 2,
  "avg_latency_ms": 1500
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |

---

### 6.5 查询 AgentEvaluation 列表

---

### GET `/api/v1/agent_monitoring/evaluations`

- **功能**：查询 AgentEvaluation 列表（分页 + 多条件筛选）
- **认证**：管理员及以上（`permission ≥ 1`）

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `≥ 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~200`，默认 `50` | 返回数量上限 |
| dimension | string | 否 | — | 按评估维度筛选 |
| min_score | float | 否 | `0.0~1.0` | 最低评分筛选 |
| max_score | float | 否 | `0.0~1.0` | 最高评分筛选 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentEvaluationListResponse`

```json
{
  "items": [AgentEvaluationResponse],
  "total": 50
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.6 获取评估统计概览

---

### GET `/api/v1/agent_monitoring/evaluations/stats`

- **功能**：获取评估统计概览
- **认证**：管理员及以上（`permission ≥ 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentEvaluationStatsResponse`

```json
{
  "total_evaluations": 100,
  "avg_score": 0.85,
  "low_score_count": 5,
  "dimension_avgs": [
    { "dimension": "accuracy", "avg_score": 0.9 }
  ]
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |

---

### 6.7 获取最近 N 天评估趋势

---

### GET `/api/v1/agent_monitoring/evaluations/trend`

- **功能**：获取最近 N 天评估趋势
- **认证**：管理员及以上（`permission ≥ 1`）

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| days | integer | 否 | `1~30`，默认 `7` | 最近天数 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentEvaluationTrendResponse`

```json
{
  "items": [
    { "date": "2026-05-26", "avg_score": 0.88, "count": 10 }
  ]
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.8 获取某 trace 下的所有评估记录

---

### GET `/api/v1/agent_monitoring/traces/{trace_id}/evaluations`

- **功能**：获取某 trace 下的所有评估记录
- **认证**：管理员及以上（`permission ≥ 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trace_id | string | 是 | Trace 唯一标识 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentEvaluationListResponse`

```json
{
  "items": [AgentEvaluationResponse],
  "total": 5
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |

---

### 6.9 手动触发对指定 trace 的评估

---

### POST `/api/v1/agent_monitoring/traces/{trace_id}/evaluate`

- **功能**：手动触发对指定 trace 的评估
- **认证**：管理员及以上（`permission ≥ 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| trace_id | string | 是 | Trace 唯一标识 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`AgentEvaluationListResponse`

```json
{
  "items": [AgentEvaluationResponse],
  "total": 5
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 404 | Trace 不存在 |
| 403 | 权限不足 |

---

### 6.10 导出 AgentTrace 数据

---

### GET `/api/v1/agent_monitoring/traces/export`

- **功能**：导出 AgentTrace 数据（JSON 或 CSV 格式）
- **认证**：管理员及以上（`permission ≥ 1`）
- **响应类型**：文件流（`application/json` 或 `text/csv; charset=utf-8`）

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| format | string | 否 | `json`/`csv`，默认 `json` | 导出格式 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：文件流，Content-Disposition 头包含文件名

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.11 导出 AgentEvaluation 数据

---

### GET `/api/v1/agent_monitoring/evaluations/export`

- **功能**：导出 AgentEvaluation 数据（JSON 或 CSV 格式）
- **认证**：管理员及以上（`permission ≥ 1`）
- **响应类型**：文件流（`application/json` 或 `text/csv; charset=utf-8`）

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| format | string | 否 | `json`/`csv`，默认 `json` | 导出格式 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：文件流，Content-Disposition 头包含文件名

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---
