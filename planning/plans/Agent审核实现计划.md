# Agent 审核实现计划

## 1. 当前项目理解

DEhub 是个人博客、作品集和社区论坛一体化平台。后端使用 FastAPI、SQLAlchemy、PostgreSQL、Redis、LangGraph/LangChain；前端使用 React 19、Vite、TypeScript。现有内容发布形态如下：

- 博客文章只有 `draft` / `published` 两种状态，发布后会生成向量索引并失效博客缓存；下线会回到草稿并删除向量索引。
- 论坛分区、帖子、回复、评论创建后立即可见，没有审核状态。
- 用户名和个人简介存储在 `users.username`、`users.personal_profile`。
- 评论当前支持 `blog_post` 与 `forum_reply` 两种目标，评论内容禁止图片。
- 项目已有 Agent 监控：`agent_traces`、`agent_spans`、`agent_evaluations`，后台已有 Agent 监控列表、详情、质量仪表盘。
- 项目已有应用级 `BackgroundTaskManager`，适合承载发布后的异步审核任务。

`planning/需求.md` 当前为空文件，本计划仅依据本次需求和现有代码结构制定。

## 2. 目标与成功标准

目标：所有文本内容发布或更新后，自动交给 AI Agent 初审；审核通过则不处理；审核不通过则自动处置，并在管理员后台看到每次审核的完整链路。

成功标准：

- 覆盖内容：用户名、个人简介、已发布博客、论坛分区名称/简介、论坛帖子标题/内容、论坛回复内容、所有评论内容。
- 不做图片审核，但文本中出现的 Markdown 图片链接不作为审核对象；保留后续扩展图片审核的字段与枚举。
- 博客审核不通过：将文章从 `published` 改为 `draft`，删除博客向量索引，失效博客缓存。
- 其它内容审核不通过：仅将被判定敏感的文本片段替换为等长或近似等长 `*`，不删除记录。
- 每次审核都有独立记录，包含对象、触发原因、审核输入快照、模型结论、命中类别、敏感片段、处置前后文本、处置结果、异常信息、关联 Agent trace。
- 异步审核失败不阻塞用户发布流程，但后台能看到失败记录并可手动重试。
- 同一内容的重复审核具备幂等保护，旧任务不能覆盖新版本内容。

## 3. 总体设计

采用“业务写入成功后异步审核”的方式，不新增内容审核期，也不改变前端发布主流程。

核心模块：

- `content_moderation_records`：审核业务记录表，面向管理员后台查询。
- `ContentModerationService`：统一入口，负责创建审核记录、调度后台任务、幂等校验、执行处置。
- `ContentModerationAgent`：专用 LangGraph 工作流，负责审核判断和产出处置方案。
- `ContentModerationPolicy`：审核 prompt 与结构化输出规则。
- `ContentSanitizer`：根据 AI 返回的敏感片段做确定性替换，避免让 LLM 直接改写数据库内容。
- `ContentModerationAdmin API`：管理员查看、筛选、详情、重试。
- 前端后台页面：在现有后台新增“内容审核”页面，并可从记录跳转到 Agent trace 详情。

推荐流程：

1. 业务服务成功提交内容。
2. 业务服务调用 `ContentModerationService.enqueue(...)` 创建 `pending` 记录。
3. `BackgroundTaskManager` 启动后台审核任务。
4. Agent 读取审核记录中的内容快照，调用小模型输出结构化审核结果。
5. 服务端验证结构化结果，执行通过或处置。
6. 更新审核记录状态，并写入 `agent_traces` / `agent_spans`。

## 4. 审核对象与触发点

| 内容类型 | 字段 | 触发点 | 不通过处置 |
|---|---|---|---|
| 用户 | `username`, `personal_profile` | 注册、管理员创建用户、用户/管理员更新资料 | 替换敏感片段 |
| 博客 | `title`, `summary`, `content_md`, `tags` | `publish_blog_post` 成功后；已发布文章更新后 | 回到 `draft` |
| 论坛分区 | `zone_name`, `description` | 创建、更新分区成功后 | 替换敏感片段 |
| 论坛帖子 | `title`, `content` | 创建、更新帖子成功后 | 替换敏感片段 |
| 论坛回复 | `content` | 创建回复成功后 | 替换敏感片段 |
| 评论 | `content` | 创建评论成功后 | 替换敏感片段 |

说明：

- 博客草稿创建和草稿更新不触发审核，只有正式发布后触发。
- 如果博客处于 `published` 状态后被更新，应重新审核更新后的内容。
- 分区、帖子、回复、评论没有审核期，审核任务完成前内容仍会短暂可见，这是本阶段接受的产品约束。
- 用户邮箱、密码、头像 URL 不进入审核范围。

## 5. 数据模型计划

新增模型 `ContentModerationRecord`，对应表 `content_moderation_records`。

建议字段：

- `id`
- `task_id`：UUID，幂等任务标识。
- `trace_id`：关联 `agent_traces.trace_id`。
- `target_type`：`user` / `blog_post` / `forum_zone` / `forum_post` / `forum_reply` / `comment`。
- `target_id`
- `target_version`：内容版本指纹，建议使用目标对象的 `updated_at` 或内容 hash。
- `trigger_action`：`create` / `update` / `publish` / `retry`。
- `status`：`pending` / `running` / `passed` / `blocked` / `action_failed` / `review_failed` / `stale`。
- `risk_level`：`none` / `low` / `medium` / `high`。
- `categories`：JSONB，例如辱骂、色情、违法、广告、隐私泄露等。
- `original_snapshot`：JSONB，审核时的字段和值。
- `moderation_result`：JSONB，模型结构化输出。
- `action_plan`：JSONB，实际要执行的处置计划。
- `action_result`：JSONB，处置后的字段和值、博客状态变化、缓存/向量处理结果。
- `model_name`
- `error_type`, `error_message`
- `created_by_user_id`
- `created_at`, `started_at`, `finished_at`

索引：

- `(target_type, target_id, created_at DESC)`
- `(status, created_at DESC)`
- `(trace_id)`
- `(target_type, target_id, target_version)` 唯一索引，避免同一版本重复审核。

文档同步：

- 新增 `planning/sql/content_moderation_records.md`。
- 新增 `planning/api-documentations/内容审核接口文档.md`。
- 若确认该机制是长期项目决策，再按规则请求用户确认后写入 `planning/需求.md`。

## 6. Agent 工作流设计

使用专用 `content_moderation_agent`，不要复用聊天 Agent 的开放式工具调用。审核 Agent 只做判断和给出处置计划，真正写库由服务端确定性执行。

建议 LangGraph 节点：

- `load_snapshot`：读取审核记录快照和目标当前版本。
- `check_staleness`：如果目标内容已被更新，标记 `stale`，避免旧审核结果覆盖新内容。
- `moderate_text`：调用小模型，要求输出严格 JSON。
- `validate_result`：校验字段、类别、敏感片段位置、置信度。
- `build_action_plan`：博客生成下线计划；其它内容生成字段级替换计划。
- `apply_action`：处置数据库内容、向量、缓存。
- `finalize_record`：写入记录状态和 span。

结构化输出要求：

- `verdict`: `pass` / `block`
- `risk_level`
- `categories`
- `reason`
- `flagged_spans`: `field`, `text`, `start`, `end`, `category`, `confidence`
- `suggested_action`: `none` / `unpublish_blog` / `mask_text`

关键约束：

- 不允许模型直接给 SQL 或调用任意工具。
- 替换只信任 `start/end` 和原文匹配成功的片段；匹配失败则降级为整字段替换或标记 `action_failed`。
- `reason` 供管理员理解，不能作为处置依据。

## 7. 处置策略

博客：

- 当前仍为 `published` 且版本匹配时，改为 `draft`。
- 调用 `BlogPostEmbeddingService.delete_post_embedding(post_id)` 删除向量。
- 调用 `BlogCacheInvalidator.invalidate_all()` 或现有博客缓存失效方法。
- 审核记录写入 `action_result.old_status = published`、`new_status = draft`。

其它文本：

- 按字段逐个替换敏感片段。
- 默认用 `*` 重复覆盖原片段长度，保留非敏感部分，避免破坏整段内容结构。
- Markdown 内容中只替换文本片段，不主动删除图片链接；如果敏感片段跨 Markdown 语法边界，允许整字段替换为同长度 `*`。
- 处置后必须调用对应缓存失效：
  - 用户资料：必要时失效依赖用户展示的博客/论坛缓存。
  - 分区：`ForumCacheInvalidator.invalidate_forum_zones()`。
  - 帖子：`ForumCacheInvalidator.invalidate_forum_posts(zone_id=...)`，详情缓存也需失效。
  - 回复：失效所属帖子相关论坛缓存。
  - 博客评论：`BlogCacheInvalidator.invalidate_blog_posts()`。

## 8. 接口与后台页面

新增管理员接口，权限要求 `permission >= ADMIN`：

- `GET /api/v1/content_moderation/records`：分页查询，支持状态、对象类型、风险等级、用户、时间筛选。
- `GET /api/v1/content_moderation/records/{id}`：详情，包含快照、模型结果、处置结果、trace 链接。
- `POST /api/v1/content_moderation/records/{id}/retry`：仅允许 `review_failed`、`action_failed`、`stale` 的记录重试。
- `GET /api/v1/content_moderation/stats`：总量、今日、失败、不通过、平均耗时。
- `GET /api/v1/content_moderation/records/export`：JSON/CSV 导出。

前端：

- 新增后台菜单“内容审核”。
- 列表展示：时间、对象类型、对象 ID、触发动作、状态、风险等级、是否已处置、模型、耗时。
- 详情展示：审核输入、命中片段、处置前后对比、异常、Agent Trace 跳转。
- 对失败记录提供“重试”按钮。

## 9. 异常处理与幂等

必须处理：

- LLM 超时或 API 失败：记录 `review_failed`，不处置内容。
- 结构化 JSON 解析失败：记录 `review_failed`，保留原始输出到 `moderation_result.raw_output`。
- 模型返回敏感片段无法定位：优先使用模糊匹配；仍失败则标记 `action_failed`，不盲目改库。
- 审核期间内容被用户更新：版本不一致时标记 `stale`，并为新版本重新入队。
- 目标对象已删除：标记 `stale` 或 `action_failed`，不报 500。
- 博客回草稿失败：记录 `action_failed`，后续允许管理员重试。
- 重复任务：通过 `(target_type, target_id, target_version)` 唯一约束防重复。
- 后台任务进程重启导致任务丢失：后续可加启动时扫描 `pending/running` 超时记录重试；首版至少提供手动重试。

## 10. 配置项

在 `Settings` 中增加：

- `CONTENT_MODERATION_ENABLED`
- `CONTENT_MODERATION_MODEL`
- `CONTENT_MODERATION_TIMEOUT`
- `CONTENT_MODERATION_MAX_TEXT_CHARS`
- `CONTENT_MODERATION_RETRY_LIMIT`
- `CONTENT_MODERATION_STALE_RUNNING_MINUTES`
- `CONTENT_MODERATION_LOG_SNAPSHOT_MAX_CHARS`

默认建议：启用、使用小模型、超时 60 秒、单次文本截断 12000 字符。

## 11. 开发步骤

1. 数据层
   - 新增 ORM、Schema、CRUD、Alembic migration、SQL 文档。
   - 验证：迁移后表结构、索引、唯一约束正确。

2. Agent 与服务层
   - 新增审核 prompt、结构化结果 Schema、LangGraph 工作流、`ContentModerationService`。
   - 验证：mock LLM 下通过、不通过、JSON 错误、超时均可落库。

3. 接入业务触发点
   - 在用户、博客、分区、帖子、回复、评论写操作成功后入队。
   - 验证：每类内容创建/更新后都有对应审核记录。

4. 自动处置
   - 实现博客回草稿和文本字段替换。
   - 验证：处置只在版本匹配时发生；缓存、向量同步处理。

5. 管理员 API
   - 新增列表、详情、统计、重试、导出。
   - 验证：普通用户 403，管理员可查询和重试。

6. 前端后台
   - 新增内容审核页面和详情页。
   - 验证：列表筛选、详情对比、trace 跳转、重试可用。

7. 文档与测试
   - 更新接口文档、SQL 文档。
   - 补充后端单元测试、集成测试和必要前端测试。

## 12. 测试计划

后端测试：

- 用户注册后触发用户名/简介审核。
- 博客发布后触发审核；不通过时状态变为 `draft` 且向量删除。
- 已发布博客更新后重新审核。
- 论坛分区、帖子、回复、评论不通过时只替换敏感片段。
- 内容更新后旧审核任务不会覆盖新内容。
- LLM 失败、JSON 失败、目标删除、处置失败均有正确记录状态。
- 管理员接口权限、分页、筛选、重试。

前端测试：

- 管理员能看到审核记录列表和统计。
- 详情页能展示命中片段、处置前后、异常和 trace 链接。
- 失败记录可以触发重试。

回归测试：

- 博客发布/下线原有行为不变。
- 论坛帖子、回复、评论计数不受审核处置影响。
- 缓存失效后前端展示处置后的内容。

## 13. 主要风险

- 发布后异步审核会有短暂违规内容可见窗口；本阶段接受，后续如需零可见窗口再引入审核期。
- LLM 误判会导致博客下线或文本被替换；因此必须保留完整记录、支持重试，并在后台清晰展示原因。
- 模型输出片段定位可能不准；必须由服务端二次校验，不允许直接信任模型改写结果。
- 原始敏感内容会进入审核记录；接口必须仅管理员可见，导出也必须受同级权限控制。
- 博客下线会影响搜索向量、首页/列表/详情缓存，处置逻辑必须复用现有发布/下线相关副作用。
- 后台任务管理器是进程内机制，生产环境多进程或重启时可能丢任务；后续如审核量提升，应迁移到 Redis 队列或 Celery/RQ。

## 14. 暂不实现

- 图片审核。
- 发布前审核期。
- 内容回滚与恢复原文。
- 用户申诉流程。
- 多模型复核。
- 自动封禁用户或扣分体系。
