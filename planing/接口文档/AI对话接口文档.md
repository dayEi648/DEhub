# AI 对话接口文档

## 1. 接口概览

### 1.1 AI 对话管理

| 方法 | 路径 | 功能简述 | 认证要求 |
|------|------|---------|---------|
| POST | `/api/v1/ai_chat/chat` | AI 对话 | 登录用户 |
| GET | `/api/v1/ai_chat/conversations` | 查询当前用户的对话列表 | 登录用户 |
| GET | `/api/v1/ai_chat/conversations/{conversation_id}/messages` | 查询某对话的消息列表 | 登录用户（仅所有者） |
| DELETE | `/api/v1/ai_chat/conversations/{conversation_id}` | 物理删除对话 | 登录用户（仅所有者） |

---

## 2. 枚举与常量定义

| 常量/枚举 | 值 | 说明 |
|-----------|-----|------|
| 默认分页 | `skip=0, limit=20` | 列表接口默认值，limit 上限 100 |
| 消息角色 `role` | `"user"` | 用户消息 |
| | `"assistant"` | AI 回复 |
| | `"system"` | 系统消息（默认隐藏，仅历史兼容或管理排查时可能出现） |
| | `"tool"` | 工具调用结果消息（默认隐藏，`include_hidden=true` 时返回） |
| Compact 提示 | `meta.compact_summary=true` | 表示后端已自动压缩模型上下文；接口只返回占位文案，不返回真实摘要内容 |

---

## 3. 统一封装返回结果

### 3.1 成功返回

后端**未**对成功响应做统一封装。接口成功时，直接返回对应 Schema 序列化后的 JSON，HTTP 状态码通常为 `200`（删除操作为 `204`）。

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
| 无权访问对话 | `403` | 无权访问该对话 | 非所有者访问他人对话 |
| 对话繁忙 | `409` | 当前对话正在生成或压缩上下文，请稍后再试 | 同一对话已有请求执行中 |
| 对话不存在 | `404` | 对话不存在 | — |
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

---

## 5. 单接口详细定义

### 5.1 AI 对话

---

### POST `/api/v1/ai_chat/chat`

- **功能**：AI 对话。传入 `conversation_id` 继续已有对话，留空则自动创建新对话并生成标题。
- **认证**：登录用户
- **并发说明**：同一对话同一时间只允许一个请求执行；AI 生成或上下文压缩期间再次发送会返回 `409`。
- **上下文压缩**：主模型回复完成后，如果上下文占用达到窗口 85%，后端会自动压缩模型上下文。压缩不会删除数据库历史消息。

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### RequestBody

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| conversation_id | integer | 否 | — | 对话 ID，留空则创建新对话 |
| user_input | string | 是 | 最小 1 字符，最大 2000 字符 | 用户输入 |
| skip_side_effects | boolean | 否 | 默认 `false` | 是否跳过标题生成、最后消息时间更新与用户画像更新等后台副作用 |
| is_edit | boolean | 否 | 默认 `false` | 已废弃兼容字段；为 `true` 时等同于 `skip_side_effects=true` |

#### 成功响应

- **状态码**：`200`
- **返回**：`ChatResponse`

```json
{
  "response": "AI 回复内容",
  "conversation_id": 42
}
```

`ChatResponse` 字段：

| 名称 | 类型 | 说明 |
|------|------|------|
| response | string | AI 回复内容 |
| conversation_id | integer | 对话 ID |

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 401 | 缺少认证令牌 |
| 404 | 对话不存在 |
| 403 | 无权访问该对话 |
| 409 | 当前对话正在生成或压缩上下文 |
| 422 | 请求参数校验失败 |

---

### 5.2 对话列表

---

### GET `/api/v1/ai_chat/conversations`

- **功能**：获取当前用户的对话列表（按最近更新时间倒序）
- **认证**：登录用户

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `≥ 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~100`，默认 `20` | 返回数量上限 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`ConversationListResponse`

```json
{
  "items": [
    {
      "id": 1,
      "title": "对话标题",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00",
      "last_message_at": "2024-01-01T00:05:00"
    }
  ],
  "total": 10
}
```

`ConversationItem` 字段：

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 对话 ID |
| title | string | 对话标题（由 LLM 自动生成） |
| created_at | string(datetime) | 创建时间 |
| updated_at | string(datetime) | 更新时间 |
| last_message_at | string(datetime) \| null | 最后消息时间 |

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 401 | 缺少认证令牌 |
| 422 | 请求参数校验失败 |

---

### 5.3 消息列表

---

### GET `/api/v1/ai_chat/conversations/{conversation_id}/messages`

- **功能**：获取某对话的消息列表（按时间正序）
- **认证**：登录用户
- **权限说明**：仅对话所有者本人可查看；对话不存在或已删除时返回 404
- **显示规则**：默认返回用户消息、有正文的 AI 回复，以及 compact 提示消息。AI 触发工具前输出的说明性正文（如“好的，我帮你联网搜索一下”）会正常返回。工具原始结果、系统消息、空内容工具决策消息默认隐藏。compact summary 的真实摘要内容不会通过该接口返回，只返回占位文案 `已自动压缩上下文`。

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | integer | 是 | 对话 ID |

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `≥ 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~500`，默认 `100` | 返回数量上限 |
| include_hidden | boolean | 否 | 默认 `false` | 是否包含隐藏的中间消息（如 tool_calls 决策消息、ToolMessage）；仅管理员或超管可用 |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`MessageResponse[]`

```json
[
  {
    "id": 1,
    "conversation_id": 1,
    "role": "user",
    "content": "你好",
    "meta": null,
    "created_at": "2024-01-01T00:00:00"
  },
  {
    "id": 2,
    "conversation_id": 1,
    "role": "assistant",
    "content": "你好！有什么可以帮你的吗？",
    "meta": null,
    "created_at": "2024-01-01T00:00:01"
  },
  {
    "id": 3,
    "conversation_id": 1,
    "role": "assistant",
    "content": "已自动压缩上下文",
    "meta": {
      "compact_summary": true
    },
    "created_at": "2024-01-01T00:00:02"
  }
]
```

`MessageResponse` 字段：

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 消息 ID |
| conversation_id | integer | 所属对话 ID |
| role | string | 角色：`user` / `assistant` / `system` / `tool` |
| content | string | 消息内容 |
| meta | object \| null | 消息元数据。普通用户默认为 `null`；compact 提示会返回 `{ "compact_summary": true }` |
| created_at | string(datetime) | 创建时间 |

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 404 | 对话不存在 |
| 403 | 无权访问该对话 |
| 403 | 非管理员请求 `include_hidden=true` |
| 422 | 请求参数校验失败 |

---

### 5.4 删除对话

---

### DELETE `/api/v1/ai_chat/conversations/{conversation_id}`

- **功能**：物理删除对话（仅对话所有者可用）。删除后同步清理 Redis Checkpointer 中的对话历史；用户长期记忆向量（用户画像摘要）保留在向量库中，供未来对话检索。
- **认证**：登录用户

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | integer | 是 | 对话 ID |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`204`
- **返回**：无

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 404 | 对话不存在 |
| 403 | 无权访问该对话 |
