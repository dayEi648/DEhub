import client from './client'
import type {
  ForumZoneCreate,
  ForumZoneUpdate,
  ForumZoneResponse,
  ForumPostCreate,
  ForumPostUpdate,
  ForumPostResponse,
  ForumPostListResponse,
  ForumReplyCreate,
  ForumReplyResponse,
  ForumReplyListResponse
} from '@/types'

export function fetchZones() {
  return client.get<ForumZoneResponse[]>('/forum_zones/')
}

export function fetchZoneById(id: number) {
  return client.get<ForumZoneResponse>(`/forum_zones/${id}`)
}

export function createZone(data: ForumZoneCreate) {
  return client.post<ForumZoneResponse>('/forum_zones/', data)
}

export function updateZone(id: number, data: ForumZoneUpdate) {
  return client.put<ForumZoneResponse>(`/forum_zones/${id}`, data)
}

export function deleteZone(id: number) {
  return client.delete(`/forum_zones/${id}`)
}

export function fetchPosts(params?: {
  zone_id?: number
  sort_by?: 'created' | 'view'
  skip?: number
  limit?: number
}) {
  return client.get<ForumPostListResponse>('/forum_posts/', { params })
}

export function fetchPostById(id: number) {
  return client.get<ForumPostResponse>(`/forum_posts/${id}`)
}

export function createPost(data: ForumPostCreate) {
  return client.post<ForumPostResponse>('/forum_posts/', data)
}

export function updatePost(id: number, data: ForumPostUpdate) {
  return client.put<ForumPostResponse>(`/forum_posts/${id}`, data)
}

export function deletePost(id: number) {
  return client.delete(`/forum_posts/${id}`)
}

export function fetchReplies(postId: number, params?: { skip?: number; limit?: number }) {
  return client.get<ForumReplyListResponse>(`/forum_posts/${postId}/replies`, { params })
}

export function createReply(postId: number, data: ForumReplyCreate) {
  return client.post<ForumReplyResponse>(`/forum_posts/${postId}/replies`, data)
}

export function deleteReply(replyId: number) {
  return client.delete(`/forum_replies/${replyId}`)
}
