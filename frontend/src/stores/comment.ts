import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { CommentResponse, CommentCreate } from '@/types'
import * as commentApi from '@/api/comment'
import { useUiStore } from './ui'

export const useCommentStore = defineStore('comment', () => {
  const uiStore = useUiStore()

  const comments = ref<CommentResponse[]>([])
  const totalComments = ref(0)
  const likedCommentIds = ref<Set<number>>(new Set())

  async function fetchComments(
    params: {
      target_type: string
      target_id: number
      parent_id?: number | null
      sort_by?: 'time' | 'hot'
      skip?: number
      limit?: number
    },
    append = false
  ) {
    const { data } = await commentApi.fetchComments(params)
    if (append) {
      const existingIds = new Set(comments.value.map((c) => c.id))
      const newItems = data.items.filter((c) => !existingIds.has(c.id))
      comments.value.push(...newItems)
      totalComments.value += newItems.length
    } else {
      comments.value = data.items
      totalComments.value = data.total
    }
    return data
  }

  async function createComment(data: CommentCreate) {
    const { data: comment } = await commentApi.createComment(data)
    if (!data.parent_id) {
      comments.value.unshift(comment)
    } else {
      comments.value.push(comment)
    }
    totalComments.value++
    uiStore.showToast('评论成功', 'success')
    return comment
  }

  async function deleteComment(id: number) {
    await commentApi.deleteComment(id)
    comments.value = comments.value.filter((c) => c.id !== id)
    totalComments.value--
    uiStore.showToast('评论已删除', 'success')
  }

  async function toggleLike(id: number) {
    const isLiked = likedCommentIds.value.has(id)
    if (isLiked) {
      await commentApi.unlikeComment(id)
      likedCommentIds.value.delete(id)
      const c = comments.value.find((item) => item.id === id)
      if (c) c.likecount--
    } else {
      await commentApi.likeComment(id)
      likedCommentIds.value.add(id)
      const c = comments.value.find((item) => item.id === id)
      if (c) c.likecount++
    }
  }

  return {
    comments,
    totalComments,
    likedCommentIds,
    fetchComments,
    createComment,
    deleteComment,
    toggleLike
  }
})
