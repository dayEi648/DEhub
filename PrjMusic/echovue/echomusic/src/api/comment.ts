import { get, post } from '@/utils/request'
import type { CommentDTO, CommentPageQuery, CommentVO } from '@/types/comment'
import type { PageDataVo } from '@/types/music'

/**
 * 分页查询评论
 */
export function getCommentPage(params: CommentPageQuery): Promise<PageDataVo<CommentVO>> {
  return get('/comments/page', params)
}

/**
 * 发表评论
 */
export function addComment(data: CommentDTO): Promise<void> {
  return post('/comments', data)
}

/**
 * 点赞/取消点赞评论
 */
export function likeComment(id: number): Promise<void> {
  return post(`/comments/${id}/like`)
}

/**
 * 点踩/取消点踩评论
 */
export function dislikeComment(id: number): Promise<void> {
  return post(`/comments/${id}/dislike`)
}
