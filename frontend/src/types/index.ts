// User types
export interface User {
  id: number
  username: string
  email: string
  created_at: string
  permission: number
  is_deleted: boolean
  avatar_url: string | null
  personal_profile: string | null
}

export interface UserBriefInfo {
  id: number
  username: string
  avatar_url: string | null
}

export type UserPermission = 0 | 1 | 2

// Blog types
export interface BlogCategory {
  id: number
  name: string
  slug: string
  description: string | null
  post_count: number
}

export interface BlogPost {
  id: number
  title: string
  slug: string
  summary: string | null
  content_md: string
  cover_image_url: string | null
  category_id: number
  category: BlogCategory
  tags: string[]
  status: 'draft' | 'published'
  view_count: number
  comment_count: number
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
  category: BlogCategory
  tags: string[]
  status: 'draft' | 'published'
  view_count: number
  comment_count: number
  created_at: string
  updated_at: string
}

// Forum types
export interface ForumZone {
  id: number
  slug: string
  zone_name: string
  description: string | null
  manager_id: number
  manager: UserBriefInfo
  view_count: number
  created_at: string
}

export interface ForumPost {
  id: number
  title: string
  content: string
  zone_id: number
  user_id: number
  user: UserBriefInfo
  view_count: number
  reply_count: number
  updated_at: string
  created_at: string
}

export interface ForumReply {
  id: number
  post_id: number
  content: string
  user_id: number
  user: UserBriefInfo
  likecount: number
  comment_count: number
  created_at: string
}

// Comment types
export interface CommentUserInfo {
  id: number
  username: string
  avatar_url: string | null
}

export interface Comment {
  id: number
  target_type: string
  target_id: number
  parent_id: number | null
  user_id: number
  content: string
  is_nested: boolean
  nested_parent_id: number | null
  likecount: number
  is_liked: boolean
  created_at: string
  user: CommentUserInfo
}

// AI Chat types
export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  last_message_at: string | null
}

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  meta: object | null
  created_at: string
}

// System Log types
export type LogLevel = 'WARN' | 'ERROR' | 'CRITICAL'

export interface SystemLog {
  id: number
  level: LogLevel
  module: string | null
  message: string
  exception: string | null
  trace_id: string | null
  user_id: number | null
  ip: string | null
  extra: object | null
  is_resolved: boolean
  resolved_at: string | null
  resolved_by: number | null
  created_at: string
}

export interface SystemLogStats {
  total: number
  total_unresolved: number
  warn_count: number
  error_count: number
  critical_count: number
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[]
  total: number
}
