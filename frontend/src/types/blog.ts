export interface BlogCategoryBrief {
  id: number
  name: string
  slug: string
}

export interface BlogCategoryWithPostCount {
  id: number
  name: string
  slug: string
  description: string | null
  post_count: number
}

export interface BlogCategoryCreateData {
  name: string
  slug?: string
  description?: string
}

export interface BlogAuthor {
  id: number
  username: string
  avatar_url: string | null
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
  comment_count: number
  user_id: number
  author: BlogAuthor
  created_at: string
  updated_at: string
}

export interface BlogPostListResponse {
  items: BlogPostListItem[]
  total: number
}

export interface BlogPostListParams {
  skip?: number
  limit?: number
  status?: string
  category_id?: number
  tag?: string
  q?: string
  include_unpublished?: boolean
}

export interface BlogPostDetailResponse extends BlogPostListItem {
  content_md: string
  prev_post: BlogPostListItem | null
  next_post: BlogPostListItem | null
}

export interface BlogPostCreateData {
  title: string
  slug?: string
  content_md: string
  category_id: number
  tags?: string[]
}

export interface BlogPostUpdateData {
  title?: string
  slug?: string
  content_md?: string
  category_id?: number
  tags?: string[]
}
