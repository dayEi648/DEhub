import client from './client'
import type {
  FavoriteStatusResponse,
  BlogPostFavoriteListResponse,
  PostFavoriteListResponse
} from '@/types'

/* ---------- Blog Post Favorites ---------- */

export function favoriteBlogPost(postId: number) {
  return client.post<FavoriteStatusResponse>(`/favorites/blog-posts/${postId}`)
}

export function unfavoriteBlogPost(postId: number) {
  return client.delete<FavoriteStatusResponse>(`/favorites/blog-posts/${postId}`)
}

export function fetchBlogPostFavorites(params?: { skip?: number; limit?: number }) {
  return client.get<BlogPostFavoriteListResponse>('/favorites/blog-posts', { params })
}

/* ---------- Forum Post Favorites ---------- */

export function favoriteForumPost(postId: number) {
  return client.post<FavoriteStatusResponse>(`/favorites/forum-posts/${postId}`)
}

export function unfavoriteForumPost(postId: number) {
  return client.delete<FavoriteStatusResponse>(`/favorites/forum-posts/${postId}`)
}

export function fetchForumPostFavorites(params?: { skip?: number; limit?: number }) {
  return client.get<PostFavoriteListResponse>('/favorites/forum-posts', { params })
}
