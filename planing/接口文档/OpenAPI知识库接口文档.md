# OpenAPI 知识库接口文档

## 接口基址

所有接口均以 `/api/v1/openapi_knowledge` 为前缀。

## 通用说明

- 所有接口均要求登录，且仅管理员及以上权限可访问。
- 普通用户访问任意接口均返回 `403 Forbidden`。
- 向量检索依赖 PostgreSQL + pgvector，维度与 `EMBEDDING_DIMENSION_EFFECTIVE` 一致（默认 1024）。

---

## 枚举

### `OpenAPIDocumentStatus`

| 值 | 说明 |
|----|------|
| `pending` | 文档已创建，等待解析 |
| `processing` | 后台正在解析和向量化 |
| `completed` | 解析和向量入库完成 |
| `failed` | 解析或向量入库失败 |

---

## 接口列表

### 1. 上传 OpenAPI 文档

- **方法**: `POST`
- **路径**: `/documents/upload`
- **权限**: 管理员及以上

**请求**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | file | 是 | OpenAPI/Swagger 文档，支持 `.json`、`.yaml`、`.yml`，限制 10MB |

**成功响应** (`200 OK`):

```json
{
  "document_id": 1,
  "filename": "openapi.yaml",
  "status": "pending"
}
```

**失败**:

| 状态码 | 原因 |
|--------|------|
| 400 | 未上传文件、空文件、格式不支持 |
| 401 | 未登录 |
| 403 | 非管理员 |
| 413 | 文件超过大小限制 |

**说明**:
- 上传后创建文档记录，状态为 `pending`。
- 重复文件（`content_hash` 相同）会覆盖旧文档及其端点向量。
- 后台自动启动解析和向量入库任务，前端可通过 `GET /documents/{document_id}` 轮询状态。

---

### 2. 分页查看文档列表

- **方法**: `GET`
- **路径**: `/documents`
- **权限**: 管理员及以上

**Query 参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skip` | int | 否 | 默认 0 |
| `limit` | int | 否 | 默认 20，上限 100 |
| `status` | string | 否 | 按状态过滤 |

**成功响应** (`200 OK`):

```json
{
  "items": [...],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

---

### 3. 查看文档详情

- **方法**: `GET`
- **路径**: `/documents/{document_id}`
- **权限**: 管理员及以上

**成功响应** (`200 OK`):

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

**失败**:

| 状态码 | 原因 |
|--------|------|
| 404 | 文档不存在 |

---

### 4. 删除文档

- **方法**: `DELETE`
- **路径**: `/documents/{document_id}`
- **权限**: 管理员及以上

**成功响应**: `204 No Content`

**失败**:

| 状态码 | 原因 |
|--------|------|
| 404 | 文档不存在 |

**说明**:
- 删除文档时级联删除其下所有端点向量。

---

### 5. 分页查看端点列表

- **方法**: `GET`
- **路径**: `/endpoints`
- **权限**: 管理员及以上

**Query 参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skip` | int | 否 | 默认 0 |
| `limit` | int | 否 | 默认 50，上限 200 |
| `document_id` | int | 否 | 按文档过滤 |
| `method` | string | 否 | 按 HTTP 方法过滤 |
| `tag` | string | 否 | 按标签过滤 |

**成功响应** (`200 OK`):

```json
{
  "items": [...],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

---

### 6. 手动检索 OpenAPI 知识库

- **方法**: `GET`
- **路径**: `/search`
- **权限**: 管理员及以上

**Query 参数**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 是 | 检索问题或关键词，最小长度 1 |
| `top_k` | int | 否 | 默认 5，上限 20 |
| `method` | string | 否 | 可选 HTTP 方法过滤 |
| `document_id` | int | 否 | 可选文档过滤 |

**成功响应** (`200 OK`):

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

**失败**:

| 状态码 | 原因 |
|--------|------|
| 422 | `q` 为空或长度不足 |

---

### 7. 删除单个端点

- **方法**: `DELETE`
- **路径**: `/endpoints/{endpoint_id}`
- **权限**: 管理员及以上

**成功响应**: `204 No Content`

**失败**:

| 状态码 | 原因 |
|--------|------|
| 404 | 端点不存在 |

---

## 权限矩阵

| 接口 | 普通用户 | 管理员 | 超级管理员 |
|------|---------|--------|-----------|
| POST /documents/upload | 403 | 允许 | 允许 |
| GET /documents | 403 | 允许 | 允许 |
| GET /documents/{id} | 403 | 允许 | 允许 |
| DELETE /documents/{id} | 403 | 允许 | 允许 |
| GET /endpoints | 403 | 允许 | 允许 |
| GET /search | 403 | 允许 | 允许 |
| DELETE /endpoints/{id} | 403 | 允许 | 允许 |

---

## Agent 工具可见性

| 工具 | 普通用户 | 管理员 |
|------|---------|--------|
| `search_blog` | 可见 | 可见 |
| `search_web` | 可见 | 可见 |
| `search_openapi_docs` | 不可见 | 可见 |
| `generate_openapi_call_example` | 不可见 | 可见 |

---

## Prompt 权限注入

- 普通用户对话中，System Prompt 不包含任何 OpenAPI 知识库能力描述。
- 管理员及以上对话中，System Prompt 追加 `<admin_capabilities>` 段落，声明 OpenAPI 知识库访问权限和使用约束。
