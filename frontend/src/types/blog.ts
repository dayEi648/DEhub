export interface BlogCategoryBrief {
  id: number
  name: string
  slug: string
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
