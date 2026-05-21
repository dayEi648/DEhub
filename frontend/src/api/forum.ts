/** ============================================================
 *  论坛相关 API 封装
 *  依据 planing/接口文档/论坛分区接口文档.md
 *       planing/接口文档/论坛帖子接口文档.md
 *       planing/接口文档/论坛回复接口文档.md
 *  ============================================================ */

import { apiFetch, buildQueryString } from './client';
import type {
  ForumZoneResponse,
  ForumZoneCreate,
  ForumZoneUpdate,
  ForumPostResponse,
  ForumPostListResponse,
  ForumPostCreate,
  ForumPostUpdate,
  ForumPostQueryParams,
  ForumReplyResponse,
  ForumReplyListResponse,
  ForumReplyContent,
} from './types';

const ZONES_BASE = '/api/v1/forum_zones';
const POSTS_BASE = '/api/v1/forum_posts';

// ===================== 论坛分区 API =====================

/** 查询所有分区列表 */
export function listForumZones(): Promise<ForumZoneResponse[]> {
  return apiFetch(`${ZONES_BASE}/`);
}

/** 根据 ID 查询分区详情 */
export function getForumZoneById(zoneId: number): Promise<ForumZoneResponse> {
  return apiFetch(`${ZONES_BASE}/${zoneId}`);
}

/** 根据 slug 查询分区详情（SEO 友好） */
export function getForumZoneBySlug(slug: string): Promise<ForumZoneResponse> {
  return apiFetch(`${ZONES_BASE}/by-slug/${slug}`);
}

/** 创建分区（管理员及以上） */
export function createForumZone(data: ForumZoneCreate): Promise<ForumZoneResponse> {
  return apiFetch(`${ZONES_BASE}/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** 编辑分区（管理员及以上 或 区主） */
export function updateForumZone(
  zoneId: number,
  data: ForumZoneUpdate
): Promise<ForumZoneResponse> {
  return apiFetch(`${ZONES_BASE}/${zoneId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/** 删除分区（管理员及以上） */
export function deleteForumZone(zoneId: number): Promise<void> {
  return apiFetch(`${ZONES_BASE}/${zoneId}`, { method: 'DELETE' });
}

// ===================== 论坛帖子 API =====================

/** 发表帖子（登录用户） */
export function createForumPost(data: ForumPostCreate): Promise<ForumPostResponse> {
  return apiFetch(`${POSTS_BASE}/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** 查询帖子列表（支持分区筛选、排序与分页） */
export function listForumPosts(params: ForumPostQueryParams = {}): Promise<ForumPostListResponse> {
  return apiFetch(`${POSTS_BASE}/${buildQueryString(params)}`);
}

/** 查询帖子详情（同时增加浏览量） */
export function getForumPostById(postId: number): Promise<ForumPostResponse> {
  return apiFetch(`${POSTS_BASE}/${postId}`);
}

/** 编辑帖子（作者本人或管理员及以上） */
export function updateForumPost(
  postId: number,
  data: ForumPostUpdate
): Promise<ForumPostResponse> {
  return apiFetch(`${POSTS_BASE}/${postId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/** 删除帖子（作者本人、管理员或区主） */
export function deleteForumPost(postId: number): Promise<void> {
  return apiFetch(`${POSTS_BASE}/${postId}`, { method: 'DELETE' });
}

// ===================== 论坛回复 API =====================

/** 发表回复（登录用户） */
export function createForumReply(
  postId: number,
  data: ForumReplyContent
): Promise<ForumReplyResponse> {
  return apiFetch(`${POSTS_BASE}/${postId}/replies`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/** 查询某帖子下的回复列表（分页） */
export function listForumReplies(
  postId: number,
  skip = 0,
  limit = 20
): Promise<ForumReplyListResponse> {
  return apiFetch(`${POSTS_BASE}/${postId}/replies?skip=${skip}&limit=${limit}`);
}

/** 删除回复（作者本人、管理员或区主） */
export function deleteForumReply(replyId: number): Promise<void> {
  return apiFetch(`/api/v1/forum_replies/${replyId}`, { method: 'DELETE' });
}
