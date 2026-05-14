import client from './client'
import type {
  BlogPostCreate,
  BlogPostUpdate,
  BlogPostResponse,
  BlogPostDetailResponse,
  BlogPostListResponse,
  BlogCategoryCreate,
  BlogCategoryUpdate,
  BlogCategoryWithPostCount
} from '@/types'

export function fetchPosts(params?: {
  skip?: number
  limit?: number
  status?: string
  category_id?: number
  tag?: string
  q?: string
  include_unpublished?: boolean
}) {
  return client.get<BlogPostListResponse>('/blog_posts/', { params })
}

export function fetchPostById(id: number) {
  return client.get<BlogPostDetailResponse>(`/blog_posts/${id}`)
}

export function fetchPostBySlug(slug: string) {
  return client.get<BlogPostDetailResponse>(`/blog_posts/by-slug/${slug}`)
}

export function createPost(data: BlogPostCreate) {
  return client.post<BlogPostResponse>('/blog_posts/', data)
}

export function updatePost(id: number, data: BlogPostUpdate) {
  return client.put<BlogPostResponse>(`/blog_posts/${id}`, data)
}

export function deletePost(id: number) {
  return client.delete(`/blog_posts/${id}`)
}

export function hardDeletePost(id: number) {
  return client.delete(`/blog_posts/${id}/hard`)
}

export function publishPost(id: number) {
  return client.post<BlogPostResponse>(`/blog_posts/${id}/publish`)
}

export function unpublishPost(id: number) {
  return client.post<BlogPostResponse>(`/blog_posts/${id}/unpublish`)
}

export function cleanupDeletedPosts() {
  return client.delete<{ deleted_count: number }>('/blog_posts/cleanup')
}

export function fetchCategories() {
  return client.get<BlogCategoryWithPostCount[]>('/blog_categories/')
}

export function createCategory(data: BlogCategoryCreate) {
  return client.post<BlogCategoryWithPostCount>('/blog_categories/', data)
}

export function updateCategory(id: number, data: BlogCategoryUpdate) {
  return client.put<BlogCategoryWithPostCount>(`/blog_categories/${id}`, data)
}

export function deleteCategory(id: number) {
  return client.delete(`/blog_categories/${id}`)
}
