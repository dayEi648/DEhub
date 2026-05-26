import request from '../utils/request'
import type {
  BlogPostListResponse,
  BlogPostListParams,
  BlogPostDetailResponse,
  BlogCategoryWithPostCount,
  BlogCategoryCreateData,
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

export function createBlogCategory(data: BlogCategoryCreateData) {
  return request.post<BlogCategoryWithPostCount>('/blog_categories/', data)
}

/* ─── Blog Post Management (Super Admin) ─── */

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

export function createBlogPost(data: BlogPostCreateData, file: File) {
  const formData = new FormData()
  formData.append('post_in', JSON.stringify(data))
  if (file) {
    formData.append('file', file)
  }
  return request.post<BlogPostDetailResponse>('/blog_posts/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function updateBlogPost(postId: number, data: BlogPostUpdateData, file?: File) {
  const formData = new FormData()
  formData.append('post_in', JSON.stringify(data))
  if (file) {
    formData.append('file', file)
  }
  return request.put<BlogPostDetailResponse>(`/blog_posts/${postId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteBlogPost(postId: number) {
  return request.delete(`/blog_posts/${postId}`)
}

export function publishBlogPost(postId: number) {
  return request.post<BlogPostDetailResponse>(`/blog_posts/${postId}/publish`)
}

export function unpublishBlogPost(postId: number) {
  return request.post<BlogPostDetailResponse>(`/blog_posts/${postId}/unpublish`)
}

