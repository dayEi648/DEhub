import request from '../utils/request'
import type {
  ForumPostListResponse,
  ForumPostListParams,
  ForumPost,
  ForumPostCreateData,
  ForumPostUpdateData,
  ForumZone,
  ForumReplyListResponse,
  ForumReplyListParams,
  ForumReply,
  ForumReplyCreateData,
} from '../types/forum'

/* ─── Forum Zones ─── */
export function getForumZoneList() {
  return request.get<ForumZone[]>('/forum_zones/')
}

export function getForumZoneBySlug(slug: string) {
  return request.get<ForumZone>(`/forum_zones/by-slug/${slug}`)
}

export function getForumZoneById(zoneId: number) {
  return request.get<ForumZone>(`/forum_zones/${zoneId}`)
}

/* ─── Forum Posts ─── */
export function getForumPostList(params: ForumPostListParams = {}) {
  return request.get<ForumPostListResponse>('/forum_posts/', { params })
}

export function getForumPostById(postId: number) {
  return request.get<ForumPost>(`/forum_posts/${postId}`)
}

export function createForumPost(data: ForumPostCreateData) {
  return request.post<ForumPost>('/forum_posts/', data)
}

export function updateForumPost(postId: number, data: ForumPostUpdateData) {
  return request.put<ForumPost>(`/forum_posts/${postId}`, data)
}

export function deleteForumPost(postId: number) {
  return request.delete(`/forum_posts/${postId}`)
}

/* ─── Forum Replies ─── */
export function getForumReplies(postId: number, params: ForumReplyListParams = {}) {
  return request.get<ForumReplyListResponse>(`/forum_posts/${postId}/replies`, { params })
}

export function createForumReply(postId: number, data: ForumReplyCreateData) {
  return request.post<ForumReply>(`/forum_posts/${postId}/replies`, data)
}

export function deleteForumReply(replyId: number) {
  return request.delete(`/forum_replies/${replyId}`)
}
