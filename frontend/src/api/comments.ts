import request from '../utils/request'
import type {
  CommentResponse,
  CommentListResponse,
  CommentListParams,
  CommentCreateData,
} from '../types/comments'

export function getCommentList(params: CommentListParams) {
  return request.get<CommentListResponse>('/comments/', { params })
}

export function createComment(data: CommentCreateData) {
  return request.post<CommentResponse>('/comments/', data)
}

export function deleteComment(commentId: number) {
  return request.delete(`/comments/${commentId}`)
}

export function likeComment(commentId: number) {
  return request.post(`/comments/${commentId}/like`)
}

export function unlikeComment(commentId: number) {
  return request.delete(`/comments/${commentId}/like`)
}
