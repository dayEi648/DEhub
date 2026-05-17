import { ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  BlogPostListItem,
  BlogPostDetailResponse,
  BlogCategoryWithPostCount,
  BlogPostCreate,
  BlogPostUpdate
} from '@/types'
import * as blogApi from '@/api/blog'
import { useUiStore } from './ui'

export const useBlogStore = defineStore('blog', () => {
  const uiStore = useUiStore()

  const posts = ref<BlogPostListItem[]>([])
  const currentPost = ref<BlogPostDetailResponse | null>(null)
  const categories = ref<BlogCategoryWithPostCount[]>([])
  const totalPosts = ref(0)
  const currentQuery = ref<Record<string, any>>({})

  async function fetchPosts(query?: {
    skip?: number
    limit?: number
    status?: string
    category_id?: number
    tag?: string
    q?: string
    include_unpublished?: boolean
  }) {
    currentQuery.value = query || {}
    const { data } = await blogApi.fetchPosts(query)
    posts.value = data.items
    totalPosts.value = data.total
    return data
  }

  async function fetchPostBySlug(slug: string) {
    const { data } = await blogApi.fetchPostBySlug(slug)
    currentPost.value = data
    return data
  }

  async function fetchCategories() {
    const { data } = await blogApi.fetchCategories()
    categories.value = data
    return data
  }

  async function createPost(data: BlogPostCreate, file?: File) {
    const formData = new FormData()
    formData.append('post_in', JSON.stringify(data))
    if (file) formData.append('file', file)
    const { data: post } = await blogApi.createPost(formData)
    uiStore.showToast('创建成功', 'success')
    return post
  }

  async function updatePost(id: number, data: BlogPostUpdate, file?: File) {
    const formData = new FormData()
    formData.append('post_in', JSON.stringify(data))
    if (file) formData.append('file', file)
    const { data: post } = await blogApi.updatePost(id, formData)
    uiStore.showToast('更新成功', 'success')
    return post
  }

  async function deletePost(id: number) {
    await blogApi.deletePost(id)
    posts.value = posts.value.filter((p) => p.id !== id)
    uiStore.showToast('已删除', 'success')
  }

  async function publishPost(id: number) {
    const { data } = await blogApi.publishPost(id)
    const idx = posts.value.findIndex((p) => p.id === id)
    if (idx !== -1) posts.value[idx].status = 'published'
    if (currentPost.value?.id === id) currentPost.value.status = 'published'
    uiStore.showToast('已发布', 'success')
    return data
  }

  async function unpublishPost(id: number) {
    const { data } = await blogApi.unpublishPost(id)
    const idx = posts.value.findIndex((p) => p.id === id)
    if (idx !== -1) posts.value[idx].status = 'draft'
    if (currentPost.value?.id === id) currentPost.value.status = 'draft'
    uiStore.showToast('已下线', 'success')
    return data
  }

  async function createCategory(data: { name: string; slug: string; description?: string | null | undefined }) {
    const { data: cat } = await blogApi.createCategory(data)
    categories.value.push(cat)
    uiStore.showToast('分类创建成功', 'success')
    return cat
  }

  async function updateCategory(id: number, data: { name?: string; slug?: string; description?: string | null }) {
    const { data: cat } = await blogApi.updateCategory(id, data)
    const idx = categories.value.findIndex((c) => c.id === id)
    if (idx !== -1) categories.value[idx] = cat
    uiStore.showToast('分类更新成功', 'success')
    return cat
  }

  async function deleteCategory(id: number) {
    await blogApi.deleteCategory(id)
    categories.value = categories.value.filter((c) => c.id !== id)
    uiStore.showToast('分类已删除', 'success')
  }

  return {
    posts,
    currentPost,
    categories,
    totalPosts,
    currentQuery,
    fetchPosts,
    fetchPostBySlug,
    fetchCategories,
    createPost,
    updatePost,
    deletePost,
    publishPost,
    unpublishPost,
    createCategory,
    updateCategory,
    deleteCategory
  }
})
