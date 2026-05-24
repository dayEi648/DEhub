import type { UserBriefInfo } from './user'

/* ─── Forum Zone ─── */
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

/* ─── Forum Post ─── */
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

export interface ForumPostListItem {
  id: number
  title: string
  zone_id: number
  user_id: number
  user: UserBriefInfo
  view_count: number
  reply_count: number
  updated_at: string
  created_at: string
}

export interface ForumPostListResponse {
  items: ForumPostListItem[]
  total: number
}

export interface ForumPostListParams {
  zone_id?: number
  sort_by?: 'created' | 'view'
  skip?: number
  limit?: number
}

export interface ForumPostCreateData {
  title: string
  content: string
  zone_id: number
}

export interface ForumPostUpdateData {
  title?: string
  content?: string
  zone_id?: number
}

/* ─── Forum Reply ─── */
export interface ForumReply {
  id: number
  post_id: number
  content: string
  user_id: number
  user: UserBriefInfo
  likecount: number
  comment_count: number
  created_at: string
  is_liked: boolean
}

export interface ForumReplyListResponse {
  items: ForumReply[]
  total: number
}

export interface ForumReplyListParams {
  skip?: number
  limit?: number
}

export interface ForumReplyCreateData {
  content: string
}
