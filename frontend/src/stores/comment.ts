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
      is_nested?: boolean
      nested_parent_id?: number
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
    } else {
      comments.value = data.items
    }
    return data
  }

  async function createComment(data: CommentCreate) {
    const { data: comment } = await commentApi.createComment(data)
    comment.is_liked = false
    if (!data.parent_id) {
      // 表层评论插到最前面
      comments.value.unshift(comment)
    } else if (data.is_nested) {
      // 嵌套回复：追加到列表末尾即可，由组件自行筛选展示
      comments.value.push(comment)
    } else {
      // 里层回复：追加到列表末尾
      comments.value.push(comment)
    }
    uiStore.showToast('评论成功', 'success')
    return comment
  }

  async function deleteComment(id: number) {
    const deleted = comments.value.find((c) => c.id === id)
    await commentApi.deleteComment(id)
    // 如果被删除的是博客表层评论，后端会级联删除其下所有子评论
    // 前端同步清理，保持状态一致
    if (
      deleted &&
      deleted.target_type === 'blog_post' &&
      deleted.parent_id === null
    ) {
      comments.value = comments.value.filter(
        (c) => c.id !== id && c.parent_id !== id
      )
    } else {
      comments.value = comments.value.filter((c) => c.id !== id)
    }
    uiStore.showToast('评论已删除', 'success')
  }

  async function toggleLike(id: number) {
    const c = comments.value.find((item) => item.id === id)
    const isLiked = c?.is_liked ?? likedCommentIds.value.has(id)
    if (isLiked) {
      await commentApi.unlikeComment(id)
      if (c) {
        c.is_liked = false
        c.likecount--
      }
      likedCommentIds.value.delete(id)
    } else {
      await commentApi.likeComment(id)
      if (c) {
        c.is_liked = true
        c.likecount++
      }
      likedCommentIds.value.add(id)
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
