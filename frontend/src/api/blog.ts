/** ============================================================
 *  博客相关 API 封装
 *  依据 planing/接口文档/博客文章接口文档.md + 博客分类接口文档.md
 *  ============================================================ */

import { apiFetch, buildQueryString } from './client';
import type {
  BlogCategoryWithPostCount,
  BlogPostListItem,
  BlogPostListResponse,
  BlogPostDetailResponse,
  BlogPostCreate,
  BlogPostUpdate,
  BlogPostQueryParams,
  GenerateSummaryRequest,
  GenerateSummaryResponse,
} from './types';

const BLOG_CATEGORIES_BASE = '/api/v1/blog_categories/';
const BLOG_POSTS_BASE = '/api/v1/blog_posts';

// ===================== 博客分类 API =====================

/** 查询所有分类列表 */
export function listBlogCategories(): Promise<BlogCategoryWithPostCount[]> {
  return apiFetch(BLOG_CATEGORIES_BASE);
}

// ===================== 博客文章 API =====================

/** 创建博客文章（超管，multipart/form-data） */
export function createBlogPost(
  postIn: BlogPostCreate,
  file?: File
): Promise<BlogPostListItem> {
  const form = new FormData();
  form.append('post_in', JSON.stringify(postIn));
  if (file) {
    form.append('file', file);
  }
  return apiFetch(`${BLOG_POSTS_BASE}/`, {
    method: 'POST',
    body: form,
  });
}

/** 发布博客文章（超管） */
export function publishBlogPost(postId: number): Promise<BlogPostListItem> {
  return apiFetch(`${BLOG_POSTS_BASE}/${postId}/publish`, { method: 'POST' });
}

/** 下线博客文章（超管） */
export function unpublishBlogPost(postId: number): Promise<BlogPostListItem> {
  return apiFetch(`${BLOG_POSTS_BASE}/${postId}/unpublish`, { method: 'POST' });
}

/** 更新博客文章（超管，multipart/form-data） */
export function updateBlogPost(
  postId: number,
  postIn: BlogPostUpdate,
  file?: File
): Promise<BlogPostListItem> {
  const form = new FormData();
  form.append('post_in', JSON.stringify(postIn));
  if (file) {
    form.append('file', file);
  }
  return apiFetch(`${BLOG_POSTS_BASE}/${postId}`, {
    method: 'PUT',
    body: form,
  });
}

/** 删除博客文章（超管） */
export function deleteBlogPost(postId: number): Promise<void> {
  return apiFetch(`${BLOG_POSTS_BASE}/${postId}`, { method: 'DELETE' });
}

/** 查看单篇博客详情（ID） */
export function getBlogPostById(postId: number): Promise<BlogPostDetailResponse> {
  return apiFetch(`${BLOG_POSTS_BASE}/${postId}`);
}

/** 查看单篇博客详情（slug） */
export function getBlogPostBySlug(slug: string): Promise<BlogPostDetailResponse> {
  return apiFetch(`${BLOG_POSTS_BASE}/by-slug/${slug}`);
}

/** 列出博客文章列表 */
export function listBlogPosts(params: BlogPostQueryParams = {}): Promise<BlogPostListResponse> {
  return apiFetch(`${BLOG_POSTS_BASE}/${buildQueryString(params)}`);
}

/** AI 自动生成摘要（超管） */
export function generateSummary(data: GenerateSummaryRequest): Promise<GenerateSummaryResponse> {
  return apiFetch(`${BLOG_POSTS_BASE}/generate-summary`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
