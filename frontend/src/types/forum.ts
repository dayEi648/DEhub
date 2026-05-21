import type { UserBriefInfo } from './user'

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

export interface ForumPostListResponse {
  items: ForumPost[]
  total: number
}

export interface ForumPostListParams {
  zone_id?: number
  sort_by?: 'created' | 'view'
  skip?: number
  limit?: number
}

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
