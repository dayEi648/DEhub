# OpenAPI 知识库接口文档

## 1. 接口概览

### 1.1 OpenAPI 知识库管理

| 方法 | 路径 | 功能简述 | 认证要求 |
|------|------|---------|---------|
| POST | `/api/v1/openapi_knowledge/documents/upload` | 上传 OpenAPI 文档并启动后台解析 | 管理员及以上 |
| GET | `/api/v1/openapi_knowledge/documents` | 分页查看 OpenAPI 文档列表 | 管理员及以上 |
| GET | `/api/v1/openapi_knowledge/documents/{document_id}` | 查看单个文档详情和解析状态 | 管理员及以上 |
| DELETE | `/api/v1/openapi_knowledge/documents/{document_id}` | 删除文档及其所有端点向量 | 管理员及以上 |
| GET | `/api/v1/openapi_knowledge/endpoints` | 分页查看端点列表 | 管理员及以上 |
| GET | `/api/v1/openapi_knowledge/search` | 手动检索 OpenAPI 知识库 | 管理员及以上 |
| DELETE | `/api/v1/openapi_knowledge/endpoints/{endpoint_id}` | 删除单个端点向量 | 管理员及以上 |

---

## 2. 枚举与常量定义

### `OpenAPIDocumentStatus`

| 值 | 说明 |
|----|------|
| `pending` | 文档已创建，等待解析 |
| `processing` | 后台正在解析和向量化 |
| `completed` | 解析和向量入库完成 |
| `failed` | 解析或向量入库失败 |

### 默认分页

| 接口 | 默认分页 | limit 上限 |
|------|---------|-----------|
| GET `/documents` | `skip=0, limit=20` | `100` |
| GET `/endpoints` | `skip=0, limit=50` | `200` |
| GET `/search` | `top_k=5` | `20` |

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
| 权限不足 | `403` | 权限不足 | 非管理员访问 |
| 文档/端点不存在 | `404` | 文档不存在 / 端点不存在 | — |
| 文件过大 | `413` | 文件超过大小限制（10MB） | 上传接口 |
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

**权限要求**：所有 OpenAPI 知识库接口均要求当前用户为**管理员及以上**（`permission >= 1`）。普通用户调用将返回 `403`。

---

## 5. 公共响应类型

### `OpenAPIDocumentResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 文档 ID |
| filename | string | 原始文件名 |
| status | string | 解析状态：`pending` / `processing` / `completed` / `failed` |
| endpoint_count | integer | 解析出的端点数量（`path x method`） |
| chunk_count | integer | 实际写入向量库的端点分片数量（去重后可能与 `endpoint_count` 不同） |
| error_message | string \| null | 解析或向量入库失败时的原因描述 |
| created_at | string(datetime) | 创建时间 |
| updated_at | string(datetime) | 更新时间 |

### `OpenAPIEndpointResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 端点 ID |
| document_id | integer | 所属 OpenAPI 文档 ID |
| chunk_id | string | 端点分片全局唯一标识，格式为 `ep_{index}_{method}_{path}_{document_id}` |
| path | string | API 路径，如 `/api/v1/users` |
| method | string | HTTP 方法，大写存储（`GET`、`POST` 等） |
| summary | string \| null | OpenAPI summary |
| description | string \| null | OpenAPI description 摘要 |
| tags | string[] \| null | OpenAPI tags |
| operation_id | string \| null | OpenAPI operationId |
| content | string | 用于 RAG 的端点文本，由解析服务生成 |
| created_at | string(datetime) | 创建时间 |
| updated_at | string(datetime) | 更新时间 |

> **注意**：端点列表接口**不暴露** `embedding` 向量字段。

### `OpenAPISearchResultResponse`

| 名称 | 类型 | 说明 |
|------|------|------|
| id | integer | 端点 ID |
| document_id | integer | 所属 OpenAPI 文档 ID |
| chunk_id | string | 端点分片唯一标识 |
| path | string | API 路径 |
| method | string | HTTP 方法 |
| summary | string \| null | OpenAPI summary |
| description | string \| null | OpenAPI description |
| tags | string[] \| null | OpenAPI tags |
| operation_id | string \| null | OpenAPI operationId |
| content | string | 用于 RAG 的端点文本 |
| similarity_score | float | 相似度得分（`0.0 ~ 1.0`），已按 `RAG_MIN_SIMILARITY` 阈值过滤 |

---

## 6. 单接口详细定义

### 6.1 上传 OpenAPI 文档

---

### POST `/api/v1/openapi_knowledge/documents/upload`

- **功能**：上传 `.json`、`.yaml`、`.yml` OpenAPI/Swagger 文档，创建文档记录并启动后台解析与向量入库
- **认证**：管理员及以上（`permission >= 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### RequestBody

`Content-Type: multipart/form-data`

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| file | file | 是 | 扩展名 `.json`/`.yaml`/`.yml`，大小 <= 10MB | OpenAPI/Swagger 文档 |

#### 成功响应

- **状态码**：`200`
- **返回**：`OpenAPIDocumentUploadResponse`

```json
{
  "document_id": 1,
  "filename": "openapi.yaml",
  "status": "pending"
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 400 | 未上传文件 / 空文件 / 格式不支持 |
| 401 | 未登录 |
| 403 | 非管理员 |
| 413 | 文件超过大小限制（10MB） |

#### 说明

- 重复文件（`content_hash` 相同）会**覆盖**旧文档及其端点向量。
- 后台自动启动解析任务，前端可通过 `GET /documents/{document_id}` 轮询 `status`。

---

### 6.2 分页查看文档列表

---

### GET `/api/v1/openapi_knowledge/documents`

- **功能**：分页查看 OpenAPI 文档列表
- **认证**：管理员及以上（`permission >= 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `>= 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~100`，默认 `20` | 返回数量上限 |
| status | string | 否 | `pending`/`processing`/`completed`/`failed` | 按解析状态过滤 |

#### 成功响应

- **状态码**：`200`
- **返回**：`OpenAPIDocumentListResponse`

```json
{
  "items": [...],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.3 查看文档详情

---

### GET `/api/v1/openapi_knowledge/documents/{document_id}`

- **功能**：查看单个文档详情和解析状态，前端上传后可通过该接口轮询 `status`
- **认证**：管理员及以上（`permission >= 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档 ID |

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### 成功响应

- **状态码**：`200`
- **返回**：`OpenAPIDocumentResponse`

```json
{
  "id": 1,
  "filename": "openapi.yaml",
  "status": "completed",
  "endpoint_count": 42,
  "chunk_count": 40,
  "error_message": null,
  "created_at": "2026-05-26T10:00:00",
  "updated_at": "2026-05-26T10:01:00"
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 404 | 文档不存在 |
| 403 | 权限不足 |

---

### 6.4 删除文档

---

### DELETE `/api/v1/openapi_knowledge/documents/{document_id}`

- **功能**：删除文档及其所有端点向量（级联删除）
- **认证**：管理员及以上（`permission >= 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| document_id | integer | 是 | 文档 ID |

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
| 404 | 文档不存在 |
| 403 | 权限不足 |

---

### 6.5 分页查看端点列表

---

### GET `/api/v1/openapi_knowledge/endpoints`

- **功能**：分页查看已入库的 OpenAPI 端点列表
- **认证**：管理员及以上（`permission >= 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| skip | integer | 否 | `>= 0`，默认 `0` | 跳过数量 |
| limit | integer | 否 | `1~200`，默认 `50` | 返回数量上限 |
| document_id | integer | 否 | — | 按所属文档过滤 |
| method | string | 否 | 如 `GET`、`POST` | 按 HTTP 方法过滤（大写） |
| tag | string | 否 | — | 按 OpenAPI tag 过滤 |

#### 成功响应

- **状态码**：`200`
- **返回**：`OpenAPIEndpointListResponse`

```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | 请求参数校验失败 |

---

### 6.6 手动检索知识库

---

### GET `/api/v1/openapi_knowledge/search`

- **功能**：基于自然语言查询语义检索 OpenAPI 端点
- **认证**：管理员及以上（`permission >= 1`）

#### Headers

| 名称 | 必填 | 说明 |
|------|------|------|
| Authorization | 是 | `Bearer <access_token>` |

#### Query 参数

| 名称 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| q | string | 是 | 最小长度 `1` | 检索问题或关键词 |
| top_k | integer | 否 | `1~20`，默认 `5` | 返回结果数量上限 |
| method | string | 否 | 如 `GET`、`POST` | 可选 HTTP 方法过滤（大写） |
| document_id | integer | 否 | — | 可选文档 ID 过滤 |

#### 成功响应

- **状态码**：`200`
- **返回**：`OpenAPISearchResponse`

```json
{
  "items": [
    {
      "id": 1,
      "document_id": 1,
      "chunk_id": "ep_0_GET_users_1",
      "path": "/users",
      "method": "GET",
      "summary": "获取用户列表",
      "description": "分页获取所有用户",
      "tags": ["user"],
      "operation_id": "listUsers",
      "content": "GET /users\nSummary: 获取用户列表...",
      "similarity_score": 0.9234
    }
  ],
  "total": 1
}
```

#### 失败响应

| 状态码 | 原因 |
|--------|------|
| 403 | 权限不足 |
| 422 | `q` 为空或长度不足 |

---

### 6.7 删除单个端点

---

### DELETE `/api/v1/openapi_knowledge/endpoints/{endpoint_id}`

- **功能**：删除单个端点向量记录
- **认证**：管理员及以上（`permission >= 1`）

#### Path 参数

| 名称 | 类型 | 必填 | 说明 |
|------|------|------|------|
| endpoint_id | integer | 是 | 端点 ID |

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
| 404 | 端点不存在 |
| 403 | 权限不足 |

---

## 7. Agent 工具可见性

| 工具 | 普通用户 | 管理员 |
|------|---------|--------|
| `search_blog` | 可见 | 可见 |
| `search_web` | 可见 | 可见 |
| `search_openapi_docs` | 不可见 | 可见 |
| `generate_openapi_call_example` | 不可见 | 可见 |

## 8. Prompt 权限注入

- 普通用户对话中，System Prompt 不包含任何 OpenAPI 知识库能力描述。
- 管理员及以上对话中，System Prompt 追加 `<admin_capabilities>` 段落，声明 OpenAPI 知识库访问权限和使用约束。
