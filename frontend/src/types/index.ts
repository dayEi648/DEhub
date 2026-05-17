/* ============================================
   Global TypeScript Types
   Aligned with backend Pydantic schemas
   ============================================ */

/* ---------- User ---------- */
export interface UserResponse {
  id: number
  username: string
  email: string
  created_at: string
  permission: number
  is_deleted: boolean
  avatar_url: string | null
  personal_profile: string | null
}

export interface UserLoginResponse {
  access_token: string
  refresh_token: string | null
  token_type: string
  user: UserResponse
  access_token_expires_in: number
  refresh_token_expires_in: number | null
}

export interface UserCreate {
  username: string
  email: string
  password: string
  permission?: number
  avatar_url?: string
  personal_profile?: string
}

export interface UserUpdate {
  username?: string
  email?: string
  password?: string
  permission?: number
  avatar_url?: string
  personal_profile?: string
}

export interface UserLogin {
  account: string
  password: string
  is_remember?: boolean
}

export interface UserBriefInfo {
  id: number
  username: string
  avatar_url: string | null
}

export interface UserListResponse {
  items: UserResponse[]
  total: number
}

/* ---------- Blog Post ---------- */
export interface BlogPostBase {
  title: string
  slug?: string
  summary: string | null
  content_md: string
  cover_image_url: string | null
  category_id: number
  tags: string[]
  status: 'draft' | 'published'
}

export interface BlogPostCreate extends BlogPostBase {}

export interface BlogPostUpdate {
  title?: string
  slug?: string
  summary?: string | null
  content_md?: string
  cover_image_url?: string | null
  category_id?: number
  tags?: string[]
  status?: 'draft' | 'published'
}

export interface BlogPostResponse extends BlogPostBase {
  id: number
  slug: string
  category: BlogCategoryBrief
  view_count: number
  created_at: string
  updated_at: string
}

export interface BlogPostListItem {
  id: number
  title: string
  slug: string
  summary: string | null
  cover_image_url: string | null
  category_id: number
  category: BlogCategoryBrief
  tags: string[]
  status: string
  view_count: number
  created_at: string
  updated_at: string
}

export interface BlogPostListResponse {
  items: BlogPostListItem[]
  total: number
}

export interface BlogPostDetailResponse extends BlogPostResponse {
  prev_post: BlogPostListItem | null
  next_post: BlogPostListItem | null
}

/* ---------- Blog Category ---------- */
export interface BlogCategoryBrief {
  id: number
  name: string
  slug: string
}

export interface BlogCategoryBase {
  name: string
  slug?: string
  description?: string | null | undefined
}

export interface BlogCategoryCreate extends BlogCategoryBase {}

export interface BlogCategoryUpdate {
  name?: string
  slug?: string
  description?: string | null
}

export interface BlogCategoryResponse extends BlogCategoryBase {
  id: number
  slug: string
}

export interface BlogCategoryWithPostCount extends BlogCategoryResponse {
  post_count: number
}

/* ---------- Forum Zone ---------- */
export interface ForumZoneBase {
  slug?: string
  zone_name: string
  description?: string | null | undefined
}

export interface ForumZoneCreate extends ForumZoneBase {
  manager_id?: number
}

export interface ForumZoneUpdate {
  slug?: string
  zone_name?: string
  description?: string | null
  manager_id?: number
}

export interface ForumZoneResponse extends ForumZoneBase {
  id: number
  slug: string
  manager_id: number
  manager: UserBriefInfo
  view_count: number
  created_at: string
}

/* ---------- Forum Post ---------- */
export interface ForumPostBase {
  title: string
  content: string
  zone_id: number
}

export interface ForumPostCreate extends ForumPostBase {}

export interface ForumPostUpdate {
  title?: string
  content?: string
  zone_id?: number
}

export interface ForumPostResponse extends ForumPostBase {
  id: number
  user_id: number
  user: UserBriefInfo
  view_count: number
  reply_count: number
  updated_at: string
  created_at: string
}

/* ---------- Forum Reply ---------- */
export interface ForumReplyBase {
  post_id: number
  content: string
}

export interface ForumReplyCreate {
  content: string
}

export interface ForumReplyResponse extends ForumReplyBase {
  id: number
  user_id: number
  user: UserBriefInfo
  likecount: number
  created_at: string
}

export interface ForumPostListResponse {
  items: ForumPostResponse[]
  total: number
}

export interface ForumReplyListResponse {
  items: ForumReplyResponse[]
  total: number
}

/* ---------- Comment ---------- */
export interface CommentUserInfo {
  id: number
  username: string
  avatar_url: string | null
}

export interface CommentCreate {
  target_type: string
  target_id: number
  parent_id?: number | null
  content: string
}

export interface CommentResponse {
  id: number
  target_type: string
  target_id: number
  parent_id: number | null
  user_id: number
  content: string
  likecount: number
  created_at: string
  user: CommentUserInfo
}

export interface CommentListResponse {
  items: CommentResponse[]
  total: number
}

/* ---------- Chat / AI ---------- */
export interface ChatCreate {
  conversation_id?: number
  user_input: string
  is_edit?: boolean
}

export interface ConversationResponse {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface MessageResponse {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  meta?: Record<string, any> | null
  created_at: string
}

export interface ConversationListResponse {
  items: ConversationResponse[]
  total: number
}

/* ---------- API Error ---------- */
export interface ApiError {
  code: number
  message: string
  detail?: any
}

/* ---------- Generic List Query ---------- */
export interface ListQuery {
  skip?: number
  limit?: number
}

/* ---------- Favorite & Follow ---------- */
export interface FavoriteStatusResponse {
  is_favorited: boolean
}

export interface FollowStatusResponse {
  is_followed: boolean
}

export interface BlogPostFavoriteListResponse {
  items: BlogPostListItem[]
  total: number
}

export interface PostFavoriteListResponse {
  items: ForumPostResponse[]
  total: number
}

export interface ZoneFollowListResponse {
  items: ForumZoneResponse[]
  total: number
}

/* ---------- System Log ---------- */
export interface SystemLogResponse {
  id: number
  level: 'WARN' | 'ERROR' | 'CRITICAL'
  module: string | null
  message: string
  exception: string | null
  trace_id: string | null
  user_id: number | null
  ip: string | null
  extra: Record<string, any> | null
  is_resolved: boolean
  resolved_at: string | null
  resolved_by: number | null
  created_at: string
}

export interface SystemLogListResponse {
  items: SystemLogResponse[]
  total: number
}

export interface SystemLogStatsResponse {
  total: number
  total_unresolved: number
  warn_count: number
  error_count: number
  critical_count: number
}
