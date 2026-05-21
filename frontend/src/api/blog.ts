import request from '../utils/request'
import type {
  BlogPostListResponse,
  BlogPostListParams,
  BlogPostDetailResponse,
  BlogCategoryWithPostCount,
} from '../types/blog'

export function getBlogPostList(params: BlogPostListParams = {}) {
  return request.get<BlogPostListResponse>('/blog_posts/', { params })
}

export function getBlogPostBySlug(slug: string) {
  return request.get<BlogPostDetailResponse>(`/blog_posts/by-slug/${slug}`)
}

export function getBlogCategories() {
  return request.get<BlogCategoryWithPostCount[]>('/blog_categories/')
}
