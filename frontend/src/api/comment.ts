import client from './client'
import type { CommentCreate, CommentResponse, CommentListResponse } from '@/types'

export function fetchComments(params: {
  target_type: string
  target_id: number
  parent_id?: number | null
  is_nested?: boolean
  nested_parent_id?: number
  sort_by?: 'time' | 'hot'
  skip?: number
  limit?: number
}) {
  return client.get<CommentListResponse>('/comments/', { params })
}

export function createComment(data: CommentCreate) {
  return client.post<CommentResponse>('/comments/', data)
}

export function deleteComment(id: number) {
  return client.delete(`/comments/${id}`)
}

export function likeComment(id: number) {
  return client.post(`/comments/${id}/like`)
}

export function unlikeComment(id: number) {
  return client.delete(`/comments/${id}/like`)
}
