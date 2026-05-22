import request from '../utils/request'
import type { BlogPostListResponse } from '../types/blog'
import type { ForumPostListResponse } from '../types/forum'
import type { ForumZone } from '../types/forum'

// ===== Blog Post Favorites =====

export function getFavoriteBlogPosts(params: { skip?: number; limit?: number } = {}) {
  return request.get<BlogPostListResponse>('/favorites/blog-posts', { params })
}

export function favoriteBlogPost(postId: number) {
  return request.post(`/favorites/blog-posts/${postId}`)
}

export function unfavoriteBlogPost(postId: number) {
  return request.delete(`/favorites/blog-posts/${postId}`)
}

// ===== Forum Post Favorites =====

export function getFavoriteForumPosts(params: { skip?: number; limit?: number } = {}) {
  return request.get<ForumPostListResponse>('/favorites/forum-posts', { params })
}

export function favoriteForumPost(postId: number) {
  return request.post(`/favorites/forum-posts/${postId}`)
}

export function unfavoriteForumPost(postId: number) {
  return request.delete(`/favorites/forum-posts/${postId}`)
}

// ===== Zone Follows =====

export interface ZoneFollowListResponse {
  items: ForumZone[]
  total: number
}

export function getFollowedZones(params: { skip?: number; limit?: number } = {}) {
  return request.get<ZoneFollowListResponse>('/follows/zones', { params })
}

export function followZone(zoneId: number) {
  return request.post(`/follows/zones/${zoneId}`)
}

export function unfollowZone(zoneId: number) {
  return request.delete(`/follows/zones/${zoneId}`)
}
