import { ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  BlogPostListItem,
  ForumPostResponse
} from '@/types'
import * as favoriteApi from '@/api/favorite'
import { useUiStore } from './ui'

export const useFavoriteStore = defineStore('favorite', () => {
  const uiStore = useUiStore()

  /* ---------- state ---------- */
  const blogFavorites = ref<BlogPostListItem[]>([])
  const forumPostFavorites = ref<ForumPostResponse[]>([])
  const blogFavoriteIds = ref<number[]>([])
  const forumPostFavoriteIds = ref<number[]>([])
  const totalBlogFavorites = ref(0)
  const totalForumPostFavorites = ref(0)

  /* ---------- blog post favorites ---------- */

  async function fetchBlogPostFavorites(query?: { skip?: number; limit?: number }) {
    const { data } = await favoriteApi.fetchBlogPostFavorites(query)
    blogFavorites.value = data.items
    totalBlogFavorites.value = data.total
    blogFavoriteIds.value = data.items.map((item) => item.id)
    return data
  }

  async function favoriteBlogPost(postId: number) {
    const { data } = await favoriteApi.favoriteBlogPost(postId)
    if (!blogFavoriteIds.value.includes(postId)) {
      blogFavoriteIds.value.push(postId)
    }
    uiStore.showToast('收藏成功', 'success')
    return data
  }

  async function unfavoriteBlogPost(postId: number) {
    const { data } = await favoriteApi.unfavoriteBlogPost(postId)
    blogFavoriteIds.value = blogFavoriteIds.value.filter((id) => id !== postId)
    blogFavorites.value = blogFavorites.value.filter((item) => item.id !== postId)
    totalBlogFavorites.value = Math.max(0, totalBlogFavorites.value - 1)
    uiStore.showToast('已取消收藏', 'success')
    return data
  }

  /* ---------- forum post favorites ---------- */

  async function fetchForumPostFavorites(query?: { skip?: number; limit?: number }) {
    const { data } = await favoriteApi.fetchForumPostFavorites(query)
    forumPostFavorites.value = data.items
    totalForumPostFavorites.value = data.total
    forumPostFavoriteIds.value = data.items.map((item) => item.id)
    return data
  }

  async function favoriteForumPost(postId: number) {
    const { data } = await favoriteApi.favoriteForumPost(postId)
    if (!forumPostFavoriteIds.value.includes(postId)) {
      forumPostFavoriteIds.value.push(postId)
    }
    uiStore.showToast('收藏成功', 'success')
    return data
  }

  async function unfavoriteForumPost(postId: number) {
    const { data } = await favoriteApi.unfavoriteForumPost(postId)
    forumPostFavoriteIds.value = forumPostFavoriteIds.value.filter((id) => id !== postId)
    forumPostFavorites.value = forumPostFavorites.value.filter((item) => item.id !== postId)
    totalForumPostFavorites.value = Math.max(0, totalForumPostFavorites.value - 1)
    uiStore.showToast('已取消收藏', 'success')
    return data
  }

  return {
    blogFavorites,
    forumPostFavorites,
    blogFavoriteIds,
    forumPostFavoriteIds,
    totalBlogFavorites,
    totalForumPostFavorites,
    fetchBlogPostFavorites,
    favoriteBlogPost,
    unfavoriteBlogPost,
    fetchForumPostFavorites,
    favoriteForumPost,
    unfavoriteForumPost
  }
})
