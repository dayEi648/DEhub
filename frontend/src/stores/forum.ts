import { ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  ForumZoneResponse,
  ForumZoneCreate,
  ForumZoneUpdate,
  ForumPostResponse,
  ForumPostCreate,
  ForumPostUpdate,
  ForumReplyResponse
} from '@/types'
import * as forumApi from '@/api/forum'
import { useUiStore } from './ui'

export const useForumStore = defineStore('forum', () => {
  const uiStore = useUiStore()

  const zones = ref<ForumZoneResponse[]>([])
  const currentZone = ref<ForumZoneResponse | null>(null)
  const posts = ref<ForumPostResponse[]>([])
  const currentPost = ref<ForumPostResponse | null>(null)
  const replies = ref<ForumReplyResponse[]>([])
  const totalPosts = ref(0)
  const totalReplies = ref(0)

  async function fetchZones() {
    const { data } = await forumApi.fetchZones()
    zones.value = data
    return data
  }

  async function fetchZoneById(id: number) {
    const { data } = await forumApi.fetchZoneById(id)
    currentZone.value = data
    return data
  }

  async function fetchPosts(params?: { zone_id?: number; sort_by?: 'created' | 'view'; skip?: number; limit?: number }) {
    const { data } = await forumApi.fetchPosts(params)
    posts.value = data.items
    totalPosts.value = data.total
    return data
  }

  async function fetchPostById(id: number) {
    const { data } = await forumApi.fetchPostById(id)
    currentPost.value = data
    return data
  }

  async function createPost(data: ForumPostCreate) {
    const { data: post } = await forumApi.createPost(data)
    posts.value.unshift(post)
    uiStore.showToast('发帖成功', 'success')
    return post
  }

  async function updatePost(id: number, data: ForumPostUpdate) {
    const { data: post } = await forumApi.updatePost(id, data)
    const idx = posts.value.findIndex((p) => p.id === id)
    if (idx !== -1) posts.value[idx] = post
    if (currentPost.value?.id === id) currentPost.value = post
    uiStore.showToast('更新成功', 'success')
    return post
  }

  async function deletePost(id: number) {
    await forumApi.deletePost(id)
    posts.value = posts.value.filter((p) => p.id !== id)
    uiStore.showToast('已删除', 'success')
  }

  async function fetchReplies(postId: number, params?: { skip?: number; limit?: number }) {
    const { data } = await forumApi.fetchReplies(postId, params)
    replies.value = data.items
    totalReplies.value = data.total
    return data
  }

  async function createReply(postId: number, content: string) {
    const { data } = await forumApi.createReply(postId, { content })
    replies.value.push(data)
    totalReplies.value++
    if (currentPost.value) currentPost.value.reply_count++
    uiStore.showToast('回复成功', 'success')
    return data
  }

  async function deleteReply(replyId: number) {
    await forumApi.deleteReply(replyId)
    replies.value = replies.value.filter((r) => r.id !== replyId)
    totalReplies.value--
    if (currentPost.value) currentPost.value.reply_count--
    uiStore.showToast('回复已删除', 'success')
  }

  async function createZone(data: ForumZoneCreate) {
    const { data: zone } = await forumApi.createZone(data)
    zones.value.push(zone)
    uiStore.showToast('分区创建成功', 'success')
    return zone
  }

  async function updateZone(id: number, data: ForumZoneUpdate) {
    const { data: zone } = await forumApi.updateZone(id, data)
    const idx = zones.value.findIndex((z) => z.id === id)
    if (idx !== -1) zones.value[idx] = zone
    uiStore.showToast('分区更新成功', 'success')
    return zone
  }

  async function deleteZone(id: number) {
    await forumApi.deleteZone(id)
    zones.value = zones.value.filter((z) => z.id !== id)
    uiStore.showToast('分区已删除', 'success')
  }

  return {
    zones,
    currentZone,
    posts,
    currentPost,
    replies,
    totalPosts,
    totalReplies,
    fetchZones,
    fetchZoneById,
    fetchPosts,
    fetchPostById,
    createPost,
    updatePost,
    deletePost,
    fetchReplies,
    createReply,
    deleteReply,
    createZone,
    updateZone,
    deleteZone
  }
})
