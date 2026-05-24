# Redis 缓存开发计划

## 1. 背景与目标

当前项目已初始化 Redis 异步与同步客户端，主要用于 JWT 黑名单、用户撤销标记、LangGraph Checkpoint 和论坛区主 ID 缓存。首页、博客主页、论坛主页等高频读场景仍直接访问 PostgreSQL，且部分接口会重复执行 join、count 和分页查询。

本计划目标是在不改变现有接口语义、不暴露草稿或用户态数据、不破坏浏览量/回复数等计数逻辑的前提下，为高频公共列表建立 Redis 缓存，降低首屏和列表页加载延迟。

本计划只描述开发方案，不直接执行业务代码实现。

## 2. 已调研代码范围

### 2.1 前端调用入口

- 首页：`frontend/src/pages/HomePage.tsx`
  - `getBlogPostList({ limit: 6, status: 'published' })`
  - `getForumPostList({ limit: 6, sort_by: 'view' })`
  - `getForumZoneList()`
- 博客主页：`frontend/src/pages/BlogListPage.tsx`
  - `getBlogPostList({ skip, limit, q, category_id })`
  - `getBlogCategories()`
- 论坛主页：`frontend/src/pages/ForumZoneListPage.tsx`
  - `getForumZoneList()`
- 分区帖子页：`frontend/src/pages/ForumPostListPage.tsx`
  - `getForumZoneBySlug(slug)`
  - `getForumPostList({ zone_id, sort_by, skip, limit })`

### 2.2 后端接口与服务

- 博客文章：`backend/app/api/v1/blog_posts.py`，`backend/app/services/blog_post_service.py`，`backend/app/crud/blog_post.py`
- 博客分类：`backend/app/api/v1/blog_categories.py`，`backend/app/services/blog_category_service.py`
- 论坛分区：`backend/app/api/v1/forum_zones.py`，`backend/app/services/forum_zone_service.py`
- 论坛帖子：`backend/app/api/v1/forum_posts.py`，`backend/app/services/forum_post_service.py`
- 论坛回复：`backend/app/services/forum_reply_service.py`
- Redis 客户端：`backend/app/redis_client.py`
- 现有分区区主缓存：`backend/app/core/zone_manager.py`

### 2.3 关键现状

- 博客列表会根据权限计算 `effective_status`。普通用户只能看到 `published`，超级管理员在 `include_unpublished=true` 时可看草稿。
- 博客详情和论坛帖子详情读取时会同步增加浏览量，不适合在首期直接整响应缓存。
- 论坛帖子列表包含 `view_count` 和 `reply_count`，这两个字段变化频繁。
- 论坛分区列表目前全量返回，包含区主信息，适合缓存，但需要在分区创建、编辑、删除、区主变更时失效。
- 博客分类列表会返回 `post_count`，当前实现统计全部文章数量。若未来希望普通用户只看到已发布文章数量，需要先单独确认产品语义；首期缓存应保持现有行为，不顺手改语义。

## 3. 总体策略

### 3.1 首期只做服务层 Cache Aside

采用 Cache Aside：

1. 读请求先查 Redis。
2. 命中后用 Pydantic response model 反序列化并返回。
3. 未命中则走现有数据库逻辑。
4. 数据库结果组装为 Pydantic 响应后写入 Redis。
5. 写操作完成数据库 commit 后执行缓存失效。
6. Redis 读写失败只记录 warning，不影响主流程。

首期不新增首页聚合接口，避免前后端联调和接口文档变更风险。首页会因为三个现有接口被缓存而受益。后续可在缓存稳定后再新增 `/api/v1/home/summary` 聚合接口减少三次 HTTP 请求。

### 3.2 不缓存或谨慎缓存的内容

- 不缓存 `GET /api/v1/blog_posts/{post_id}` 与 `GET /api/v1/blog_posts/by-slug/{slug}` 的整响应，因为读取会增加浏览量，并包含相邻文章。
- 不缓存 `GET /api/v1/forum_posts/{post_id}` 的整响应，因为读取会增加浏览量。
- 不缓存用户态接口，例如收藏、关注、当前用户点赞状态。
- 不缓存超级管理员 `include_unpublished=true` 的博客列表，避免草稿列表跨用户或跨权限复用。
- 评论列表首期不纳入，因为 `is_liked` 等用户态字段和点赞排序会让失效策略更复杂。

## 4. 缓存对象与 Key 设计

统一前缀：`dehub:cache:v1`

### 4.1 博客文章公共列表

适用接口：`GET /api/v1/blog_posts/`

缓存条件：

- `effective_status == "published"`
- `include_unpublished` 不为 true
- 不区分当前用户，因为响应不包含用户态字段

Key：

```text
dehub:cache:v1:blog_posts:list:{sha256(normalized_params)}
```

`normalized_params` 包含：

- `skip`
- `limit`
- `status=published`
- `category_id`
- `tag`
- `q`

建议 TTL：

- 首页最新博客：120 秒
- 普通分页列表：60 秒
- 搜索 `q` 非空：30 秒

失效时机：

- 创建博客且最终状态为 `published`
- 发布、下线文章
- 更新博客的标题、摘要、封面、分类、标签、状态、slug、正文
- 删除博客
- 新增或删除博客评论导致 `comment_count` 变化时，如果数据库触发器维护了 `comment_count`，也应失效博客列表

### 4.2 博客分类列表

适用接口：`GET /api/v1/blog_categories/`

Key：

```text
dehub:cache:v1:blog_categories:list
```

建议 TTL：300 秒

失效时机：

- 创建、更新、删除分类
- 博客创建、删除、发布、下线、分类变更时，因为 `post_count` 可能变化

注意：

- 首期保持现有 `post_count` 统计语义，不改变为只统计已发布文章。
- 若后续修正普通用户可见统计，需要先补接口文档和权限测试，再调整缓存 key 维度。

### 4.3 论坛分区列表与 slug 详情

适用接口：

- `GET /api/v1/forum_zones/`
- `GET /api/v1/forum_zones/by-slug/{slug}`
- 可选：`GET /api/v1/forum_zones/{zone_id}`

Key：

```text
dehub:cache:v1:forum_zones:list
dehub:cache:v1:forum_zones:slug:{slug}
dehub:cache:v1:forum_zones:id:{zone_id}
```

建议 TTL：

- 分区列表：300 秒
- 分区详情：300 秒

失效时机：

- 创建分区
- 更新分区名称、描述、slug、manager_id
- 删除分区
- 用户硬删除导致区主转移时，应清理受影响分区缓存和现有 `forum_zone:manager:{zone_id}` 缓存

注意：

- 当前分区 `view_count` 暂未看到增加逻辑，因此缓存分区 `view_count` 不会额外引入已知一致性问题。

### 4.4 论坛帖子列表

适用接口：`GET /api/v1/forum_posts/`

Key：

```text
dehub:cache:v1:forum_posts:list:{sha256(normalized_params)}
```

`normalized_params` 包含：

- `zone_id`
- `sort_by`
- `skip`
- `limit`

建议 TTL：

- `sort_by=created` 且第一页：60 秒
- `sort_by=view` 或首页热门帖子：30 秒
- 非第一页：60 秒

失效时机：

- 发帖
- 编辑帖子标题、内容、分区
- 删除帖子
- 新增或删除回复导致 `reply_count` 变化
- 帖子分区变更时同时失效旧分区和新分区相关列表

浏览量处理：

- 不在每次详情浏览后立即失效热门帖子缓存，否则热门入口会退化为频繁删缓存。
- 首期接受热门列表 `view_count` 在 30 秒内的轻微滞后。
- 若后续需要更强实时性，再设计 Redis 计数器聚合和定时回写，不在首期混入。

## 5. 缓存工具模块设计

新增建议模块：`backend/app/infrastructure/cache.py`

核心能力：

- `build_cache_key(namespace: str, params: dict) -> str`
- `get_json_cache(key: str, model_type: type[T]) -> T | None`
- `set_json_cache(key: str, value: BaseModel | list | dict, ttl: int, tags: list[str]) -> None`
- `invalidate_cache_tags(tags: list[str]) -> None`
- `safe_cache_call(...)` 或内部 try/except，Redis 异常不影响业务响应

序列化要求：

- 使用 Pydantic 响应模型的 `model_dump(mode="json")`
- 列表响应缓存 `BlogPostListResponse`、`ForumPostListResponse`
- 简单数组可缓存为 `list[ForumZoneResponse.model_dump(mode="json")]`
- 命中后必须用 response model 重新校验，避免结构漂移导致脏数据直接出接口

标签集合建议：

```text
dehub:cachetag:v1:blog_posts
dehub:cachetag:v1:blog_categories
dehub:cachetag:v1:forum_zones
dehub:cachetag:v1:forum_posts
dehub:cachetag:v1:forum_posts:zone:{zone_id}
```

失效实现：

1. 写缓存时 `SADD cachetag keys`，并为 tag set 设置略长于业务 key 的 TTL。
2. 失效时 `SMEMBERS` 获取 key 列表，批量 `DELETE` 这些 key 和 tag set。
3. 避免生产代码使用 `KEYS`；如需兜底，使用 `SCAN` 且仅用于维护脚本。

防穿透与防击穿：

- 空列表可以缓存，避免空页面重复 count。
- 404 详情首期不缓存。
- 对首页热门 key 可加短锁：`dehub:cachelock:v1:{key}`，`SET nx ex=5`。
- 未抢到锁时不阻塞主请求，可直接走数据库并跳过写缓存，保持简单可靠。

配置项建议加入 `backend/app/core/config.py`：

```text
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=60
CACHE_BLOG_LIST_TTL=60
CACHE_BLOG_HOME_TTL=120
CACHE_FORUM_ZONE_TTL=300
CACHE_FORUM_POST_LIST_TTL=60
CACHE_FORUM_HOT_POST_TTL=30
```

## 6. 分阶段实施计划

### Phase 1：缓存基础设施与单元测试

目标：

- 新增缓存工具模块。
- 提供安全读写、Pydantic JSON 序列化、tag 失效、TTL jitter、Redis 异常降级。

测试：

- key 生成对参数顺序不敏感。
- model 序列化与反序列化保持字段类型正确。
- Redis 异常时返回 miss，不抛出到业务层。
- tag 失效会删除所有登记 key。

### Phase 2：博客公共列表与分类缓存

目标：

- 在 `BlogPostService.list_blog_posts` 中仅缓存 `published` 公共列表。
- 在 `BlogCategoryService.list_categories` 中缓存分类列表。
- 在博客写操作成功后清理相关 tag。

测试：

- 普通用户请求列表：第一次查 DB，第二次命中 Redis。
- 超管 `include_unpublished=true` 不读写公共缓存。
- 发布、下线、更新、删除文章后缓存被失效。
- 分类创建、更新、删除后分类缓存被失效。
- 不同 `q`、`category_id`、`skip`、`limit` 生成不同 key。

### Phase 3：论坛分区缓存

目标：

- 缓存分区列表和 slug 详情。
- 分区创建、编辑、删除后清理分区缓存。
- 用户注销转移区主时补充分区缓存失效。

测试：

- 首页和论坛主页分区列表复用同一缓存。
- slug 详情命中缓存后仍能通过 Pydantic 校验。
- 更新分区名称、slug、manager_id 后旧缓存不可继续命中。
- 删除分区后列表缓存失效，详情缓存失效。

### Phase 4：论坛帖子列表缓存

目标：

- 缓存帖子列表分页结果。
- 对 `sort_by=view` 使用更短 TTL。
- 发帖、编辑、删帖、回复增删后清理帖子列表缓存。

测试：

- 首页热门帖子 `limit=6&sort_by=view` 可命中缓存。
- 分区帖子列表按 `zone_id`、`sort_by`、分页参数隔离缓存。
- 发帖后 `created` 列表缓存失效。
- 回复创建和删除后列表中的 `reply_count` 不长时间陈旧。
- 浏览详情只增加数据库浏览量，不立即失效热门列表，热门列表 TTL 生效。

### Phase 5：回归与性能验证

目标：

- 证明接口行为未变化，缓存只是性能优化。
- 验证 Redis 不可用时系统仍可用。

测试：

- 后端：`python -m pytest backend/tests`
- 前端只在改动接口封装或新增首页聚合接口时执行：
  - `npm run lint`
  - `npm run build`
  - `npx playwright test`
- 手工验证：
  - 首页刷新两次，第二次后端日志或测试桩显示列表命中缓存。
  - 博客发布后首页最新博客可刷新出现。
  - 论坛发帖后分区最新列表可刷新出现。
  - Redis 停止或连接失败时接口仍返回数据库结果。

## 7. 风险与规避

### 7.1 权限泄漏风险

风险：超级管理员草稿列表被缓存后普通用户命中。

规避：

- 首期只缓存 `effective_status=published` 的公共列表。
- key 不使用前端传入的原始 `status`，必须使用服务层计算后的 `effective_status`。
- 增加测试覆盖普通用户与超管请求隔离。

### 7.2 浏览量实时性风险

风险：缓存导致列表页显示的 `view_count` 滞后。

规避：

- 详情接口首期不缓存。
- 热门帖子列表 TTL 控制在 30 秒。
- 不因每次浏览详情失效列表缓存，避免热门列表高频抖动。

### 7.3 缓存失效遗漏

风险：写操作后列表继续展示旧数据。

规避：

- 失效逻辑集中封装为 `BlogCacheInvalidator`、`ForumCacheInvalidator` 或同等模块。
- 所有 service 写操作在 commit 成功后调用失效。
- 测试覆盖 create/update/delete/publish/unpublish/reply create/reply delete。

### 7.4 Redis 故障影响主流程

风险：Redis 连接异常导致接口 500。

规避：

- 缓存工具捕获 Redis 异常并记录 warning。
- Redis 故障时走数据库结果。
- 不在业务核心分支强依赖缓存成功。

### 7.5 序列化结构漂移

风险：缓存 JSON 字段与 Pydantic schema 更新后不一致。

规避：

- 命中缓存后仍用响应模型校验。
- key 前缀包含版本 `v1`，schema 破坏性变化时提升到 `v2`。
- 反序列化失败时删除该 key 并回源数据库。

## 8. 文档维护计划

实现时需要同步维护：

- `planing/directory.md`：新增缓存基础设施文件或测试文件后更新目录说明。
- 接口文档：若仅增加缓存，不改变接口输入输出，无需变更接口定义；若新增 `/api/v1/home/summary`，必须新增对应接口文档。
- 可选技术文档：缓存 key、TTL、失效策略可沉淀到 `planing/Redis缓存策略.md` 或保留在本计划中。

## 9. 建议优先级

建议按以下顺序执行：

1. 博客公共列表缓存：直接改善首页与博客主页，权限边界清晰。
2. 论坛分区缓存：数据低频变化，收益稳定，失效简单。
3. 论坛帖子列表缓存：收益高，但需要处理回复数和浏览量滞后。
4. 博客分类缓存：可与博客列表一起做，但需要关注 `post_count` 现有语义。
5. 首页聚合接口：作为二期优化，不建议首期同时引入。

## 10. 预期成果

- 首页三类内容的数据库重复查询显著减少。
- 博客主页分页与筛选在重复访问时响应更快。
- 论坛主页分区列表与热门帖子加载更稳定。
- Redis 异常不影响用户正常访问。
- 缓存策略可通过单元测试追踪，不依赖人工判断是否失效。

---

## 11. 后续修补记录（2026-05-24）

在按本计划完成 Redis 缓存基础设施与业务接入后，通过代码审查发现以下问题并已完成修补：

1. **论坛帖子列表响应瘦身**：`GET /api/v1/forum_posts/` 列表接口原返回完整 `content`，现已拆分出 `ForumPostListItem`（不含 `content`），Redis 缓存同步不再存储完整正文，降低响应体与缓存体积。
2. **博客分类更新缓存失效范围扩大**：`BlogCategoryService.update_category` 原仅失效分类缓存，现改为调用 `BlogCacheInvalidator.invalidate_all()`，同时失效博客文章列表缓存，避免分类名称/slug 变更后列表展示旧数据。
3. **用户硬删除缓存失效补全**：`UserService.hard_delete_user` 事务提交后，现同时调用 `BlogCacheInvalidator.invalidate_blog_posts()` 与 `ForumCacheInvalidator.invalidate_forum_posts()`，避免已删除用户的帖子和评论继续出现在缓存中。
4. **博客分类 TTL 语义清晰化**：新增配置项 `CACHE_BLOG_CATEGORY_TTL=300`，替代原先复用的 `CACHE_FORUM_ZONE_TTL`。
5. **热点缓存锁安全释放**：`acquire_cache_lock` 现写入随机 token 并返回；`release_cache_lock` 仅在 token 与 Redis 当前值一致时才删除，避免锁过期后被其他请求重新持有时发生误删。
