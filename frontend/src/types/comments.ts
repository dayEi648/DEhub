export interface CommentUserInfo {
  id: number
  username: string
  avatar_url: string | null
}

export interface CommentResponse {
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

export interface CommentListResponse {
  items: CommentResponse[]
  total: number
}

export interface CommentListParams {
  target_type: string
  target_id: number
  parent_id?: number
  is_nested?: boolean
  nested_parent_id?: number
  sort_by?: 'time' | 'time_asc' | 'hot'
  skip?: number
  limit?: number
}

export interface CommentCreateData {
  target_type: string
  target_id: number
  parent_id?: number
  is_nested?: boolean
  nested_parent_id?: number
  content: string
}
