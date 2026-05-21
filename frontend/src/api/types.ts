/** ============================================================
 *  用户相关接口类型定义
 *  依据 planing/接口文档/用户接口文档.md
 *  ============================================================ */

/** 用户响应 */
export interface UserResponse {
  id: number;
  username: string;
  email: string;
  created_at: string;
  permission: number;
  is_deleted: boolean;
  avatar_url: string | null;
  personal_profile: string | null;
}

/** 用户列表响应 */
export interface UserListResponse {
  items: UserResponse[];
  total: number;
}

/** 登录请求 */
export interface UserLogin {
  account: string;
  password: string;
  is_remember?: boolean;
}

/** 登录响应 */
export interface UserLoginResponse {
  access_token: string;
  refresh_token: string | null;
  token_type: string;
  user: UserResponse;
  access_token_expires_in: number;
  refresh_token_expires_in: number | null;
}

/** 注册请求 */
export interface UserRegister {
  username: string;
  email: string;
  password: string;
}

/** 登出请求 */
export interface UserLogout {
  refresh_token?: string;
}

/** 刷新令牌请求 */
export interface RefreshTokenRequest {
  refresh_token: string;
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

/** 用户更新请求（全可选） */
export interface UserUpdate {
  username?: string;
  email?: string;
  password?: string;
  permission?: number;
  avatar_url?: string;
  personal_profile?: string;
}

/** 创建用户请求 */
export interface UserCreate {
  username: string;
  email: string;
  password: string;
  permission?: number;
  avatar_url?: string;
  personal_profile?: string;
}

/** 标准错误响应 */
export interface ApiError {
  code: number;
  message: string;
  detail?: unknown;
}

/** 管理后台页面标识 */
export type AdminPage = 'users' | 'forum-zones' | 'logs';

/** ============================================================
 *  博客分类接口类型定义
 *  依据 planing/接口文档/博客分类接口文档.md
 *  ============================================================ */

/** 博客分类简要信息 */
export interface BlogCategoryBrief {
  id: number;
  name: string;
  slug: string;
}

/** 博客分类（含文章数量） */
export interface BlogCategoryWithPostCount {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  post_count: number;
}

/** 博客分类创建请求 */
export interface BlogCategoryCreate {
  name: string;
  slug?: string;
  description?: string;
}

/** 博客分类更新请求 */
export interface BlogCategoryUpdate {
  name?: string;
  slug?: string;
  description?: string;
}

/** ============================================================
 *  博客文章接口类型定义
 *  依据 planing/接口文档/博客文章接口文档.md
 *  ============================================================ */

/** 博客文章状态 */
export type BlogPostStatus = 'draft' | 'published';

/** 博客作者简要信息 */
export interface BlogAuthorBrief {
  id: number;
  username: string;
  avatar_url: string | null;
}

/** 博客文章列表项 */
export interface BlogPostListItem {
  id: number;
  user_id: number;
  title: string;
  slug: string;
  summary: string | null;
  cover_image_url: string | null;
  category_id: number;
  category: BlogCategoryBrief;
  tags: string[];
  status: BlogPostStatus;
  view_count: number;
  comment_count: number;
  created_at: string;
  updated_at: string;
  author: BlogAuthorBrief;
}

/** 博客文章列表响应 */
export interface BlogPostListResponse {
  items: BlogPostListItem[];
  total: number;
}

/** 博客文章详情响应 */
export interface BlogPostDetailResponse extends BlogPostListItem {
  content_md: string;
  prev_post: BlogPostListItem | null;
  next_post: BlogPostListItem | null;
}

/** 博客文章创建请求 */
export interface BlogPostCreate {
  title: string;
  slug?: string;
  summary?: string;
  content_md: string;
  cover_image_url?: string;
  category_id: number;
  tags?: string[];
  status?: BlogPostStatus;
}

/** 博客文章更新请求 */
export interface BlogPostUpdate {
  title?: string;
  slug?: string;
  summary?: string;
  content_md?: string;
  cover_image_url?: string;
  category_id?: number;
  tags?: string[];
  status?: BlogPostStatus;
}

/** 博客文章排序方式 */
export type BlogPostSortBy = 'latest' | 'hot';

/** 博客文章查询参数 */
export interface BlogPostQueryParams {
  skip?: number;
  limit?: number;
  status?: BlogPostStatus;
  category_id?: number;
  tag?: string;
  q?: string;
  include_unpublished?: boolean;
  sort_by?: BlogPostSortBy;
}

/** AI 生成摘要请求 */
export interface GenerateSummaryRequest {
  content_md: string;
}

/** AI 生成摘要响应 */
export interface GenerateSummaryResponse {
  summary: string;
}

/** ============================================================
 *  评论接口类型定义
 *  依据 planing/接口文档/评论接口文档.md
 *  ============================================================ */

/** 评论排序方式 */
export type CommentSortBy = 'time' | 'hot';

/** 评论者信息 */
export interface CommentUserInfo {
  id: number;
  username: string;
  avatar_url: string | null;
}

/** 评论响应 */
export interface CommentResponse {
  id: number;
  target_type: string;
  target_id: number;
  parent_id: number | null;
  user_id: number;
  content: string;
  is_nested: boolean;
  nested_parent_id: number | null;
  likecount: number;
  is_liked: boolean;
  created_at: string;
  user: CommentUserInfo;
}

/** 评论列表响应 */
export interface CommentListResponse {
  items: CommentResponse[];
  total: number;
}

/** 评论创建请求 */
export interface CommentCreate {
  target_type: string;
  target_id: number;
  parent_id?: number;
  is_nested?: boolean;
  nested_parent_id?: number;
  content: string;
}

/** 评论查询参数 */
export interface CommentQueryParams {
  target_type: string;
  target_id: number;
  parent_id?: number;
  is_nested?: boolean;
  nested_parent_id?: number;
  sort_by?: CommentSortBy;
  skip?: number;
  limit?: number;
}

/** 用户简要信息 */
export interface UserBriefInfo {
  id: number;
  username: string;
  avatar_url: string | null;
}

/** ============================================================
 *  收藏关注接口类型定义
 *  依据 planing/接口文档/收藏关注接口文档.md
 *  ============================================================ */

/** 收藏状态响应 */
export interface FavoriteStatusResponse {
  is_favorited: boolean;
}

/** 关注状态响应 */
export interface FollowStatusResponse {
  is_followed: boolean;
}

/** 博客文章收藏列表响应 */
export interface BlogPostFavoriteListResponse {
  items: BlogPostListItem[];
  total: number;
}

/** 论坛帖子排序方式 */
export type ForumPostSortBy = 'created' | 'view';

/** 论坛帖子查询参数 */
export interface ForumPostQueryParams {
  zone_id?: number;
  sort_by?: ForumPostSortBy;
  skip?: number;
  limit?: number;
}

/** 论坛帖子创建请求 */
export interface ForumPostCreate {
  title: string;
  content: string;
  zone_id: number;
}

/** 论坛帖子更新请求 */
export interface ForumPostUpdate {
  title?: string;
  content?: string;
  zone_id?: number;
}

/** 论坛帖子响应 */
export interface ForumPostResponse {
  id: number;
  title: string;
  content: string;
  zone_id: number;
  user_id: number;
  user: UserBriefInfo;
  view_count: number;
  reply_count: number;
  updated_at: string;
  created_at: string;
}

/** 论坛帖子列表响应 */
export interface ForumPostListResponse {
  items: ForumPostResponse[];
  total: number;
}

/** 论坛回复响应 */
export interface ForumReplyResponse {
  id: number;
  post_id: number;
  content: string;
  user_id: number;
  user: UserBriefInfo;
  likecount: number;
  comment_count: number;
  created_at: string;
}

/** 论坛回复列表响应 */
export interface ForumReplyListResponse {
  items: ForumReplyResponse[];
  total: number;
}

/** 论坛回复内容请求 */
export interface ForumReplyContent {
  content: string;
}

/** 论坛分区创建请求 */
export interface ForumZoneCreate {
  slug?: string;
  zone_name: string;
  description?: string;
  manager_id?: number;
}

/** 论坛分区更新请求 */
export interface ForumZoneUpdate {
  slug?: string;
  zone_name?: string;
  description?: string;
  manager_id?: number;
}

/** 论坛帖子收藏列表响应 */
export interface PostFavoriteListResponse {
  items: ForumPostResponse[];
  total: number;
}

/** 论坛分区响应 */
export interface ForumZoneResponse {
  id: number;
  slug: string;
  zone_name: string;
  description: string | null;
  manager_id: number;
  manager: UserBriefInfo;
  view_count: number;
  created_at: string;
}

/** 关注分区列表响应 */
export interface ZoneFollowListResponse {
  items: ForumZoneResponse[];
  total: number;
}

/** 论坛回复查询参数 */
export interface ForumReplyQueryParams {
  skip?: number;
  limit?: number;
}
