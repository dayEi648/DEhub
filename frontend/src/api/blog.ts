import request from '../utils/request'
import type { BlogPostListResponse, BlogPostListParams } from '../types/blog'

export function getBlogPostList(params: BlogPostListParams = {}) {
  return request.get<BlogPostListResponse>('/blog_posts/', { params })
}
