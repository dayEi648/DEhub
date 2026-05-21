/** ============================================================
 *  评论相关 API 封装
 *  依据 planing/接口文档/评论接口文档.md
 *  ============================================================ */

import { apiFetch } from './client';
import type {
  CommentResponse,
  CommentListResponse,
  CommentCreate,
  CommentQueryParams,
} from './types';

const COMMENTS_BASE = '/api/v1/comments';

/** 新增评论 */
export function createComment(data: CommentCreate): Promise<CommentResponse> {
  return apiFetch(COMMENTS_BASE, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** 删除评论 */
export function deleteComment(commentId: number): Promise<void> {
  return apiFetch(`${COMMENTS_BASE}/${commentId}`, { method: 'DELETE' });
}

/** 分页查询评论列表 */
export function listComments(params: CommentQueryParams): Promise<CommentListResponse> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      qs.append(key, String(value));
    }
  });
  const s = qs.toString();
  return apiFetch(`${COMMENTS_BASE}/${s ? `?${s}` : ''}`);
}

/** 点赞评论 */
export function likeComment(commentId: number): Promise<void> {
  return apiFetch(`${COMMENTS_BASE}/${commentId}/like`, { method: 'POST' });
}

/** 取消点赞评论 */
export function unlikeComment(commentId: number): Promise<void> {
  return apiFetch(`${COMMENTS_BASE}/${commentId}/like`, { method: 'DELETE' });
}
