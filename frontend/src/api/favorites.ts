/** ============================================================
 *  收藏关注相关 API 封装
 *  依据 planing/接口文档/收藏关注接口文档.md
 *  ============================================================ */

import { apiFetch } from './client';
import type {
  FavoriteStatusResponse,
  FollowStatusResponse,
  BlogPostFavoriteListResponse,
  PostFavoriteListResponse,
  ZoneFollowListResponse,
} from './types';

// ===================== 博客文章收藏 =====================

/** 收藏博客文章 */
export function favoriteBlogPost(postId: number): Promise<FavoriteStatusResponse> {
  return apiFetch(`/api/v1/favorites/blog-posts/${postId}`, { method: 'POST' });
}

/** 取消收藏博客文章 */
export function unfavoriteBlogPost(postId: number): Promise<FavoriteStatusResponse> {
  return apiFetch(`/api/v1/favorites/blog-posts/${postId}`, { method: 'DELETE' });
}

/** 获取博客文章收藏列表 */
export function listBlogPostFavorites(
  skip = 0,
  limit = 20
): Promise<BlogPostFavoriteListResponse> {
  return apiFetch(`/api/v1/favorites/blog-posts?skip=${skip}&limit=${limit}`);
}

// ===================== 论坛帖子收藏 =====================

/** 收藏论坛帖子 */
export function favoriteForumPost(postId: number): Promise<FavoriteStatusResponse> {
  return apiFetch(`/api/v1/favorites/forum-posts/${postId}`, { method: 'POST' });
}

/** 取消收藏论坛帖子 */
export function unfavoriteForumPost(postId: number): Promise<FavoriteStatusResponse> {
  return apiFetch(`/api/v1/favorites/forum-posts/${postId}`, { method: 'DELETE' });
}

/** 获取论坛帖子收藏列表（TODO: 论坛功能实现后接入） */
export function listForumPostFavorites(
  skip = 0,
  limit = 20
): Promise<PostFavoriteListResponse> {
  return apiFetch(`/api/v1/favorites/forum-posts?skip=${skip}&limit=${limit}`);
}

// ===================== 论坛分区关注 =====================

/** 关注论坛分区 */
export function followZone(zoneId: number): Promise<FollowStatusResponse> {
  return apiFetch(`/api/v1/follows/zones/${zoneId}`, { method: 'POST' });
}

/** 取消关注论坛分区 */
export function unfollowZone(zoneId: number): Promise<FollowStatusResponse> {
  return apiFetch(`/api/v1/follows/zones/${zoneId}`, { method: 'DELETE' });
}

/** 获取关注分区列表（TODO: 论坛功能实现后接入） */
export function listFollowedZones(
  skip = 0,
  limit = 20
): Promise<ZoneFollowListResponse> {
  return apiFetch(`/api/v1/follows/zones?skip=${skip}&limit=${limit}`);
}
