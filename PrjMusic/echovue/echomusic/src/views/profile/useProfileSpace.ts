import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

import {
  getSpacePostPage,
  addSpacePost,
  likeSpacePost,
  forwardSpacePost,
  deleteSpacePost
} from '@/api/spacePost'
import { getUser } from '@/utils/authStorage'
import { get } from '@/utils/request'
import type { SpacePostVO, SpacePostDTO, SpacePostForwardDTO } from '@/types/spacePost'
import type { UserVO } from '@/types/user'

export function useProfileSpace() {
  const currentUser = computed(() => getUser())

  // ========== 说说列表 ==========
  const posts = ref<SpacePostVO[]>([])
  const total = ref(0)
  const pageNum = ref(1)
  const pageSize = ref(10)
  const loading = ref(false)

  // ========== 统计数据 ==========
  const stats = ref({ postCount: 0, likeCount: 0 })

  // ========== 发表区 ==========
  const showPublishArea = ref(false)
  const publishContent = ref('')
  const publishImages = ref<string[]>([])
  const mentionUserIds = ref<number[]>([])
  const mentionUserMap = ref<Record<string, number>>({})
  const isPublishing = ref(false)
  const imageUploading = ref(false)

  // ========== 转发 ==========
  const showForwardDialog = ref(false)
  const forwardTarget = ref<SpacePostVO | null>(null)
  const forwardContent = ref('')
  const isForwarding = ref(false)

  // ========== 评论展开 ==========
  const activeCommentPostId = ref<number | null>(null)

  // ========== @提及搜索 ==========
  const showMentionDialog = ref(false)
  const mentionKeyword = ref('')
  const mentionLoading = ref(false)
  const mentionUsers = ref<UserVO[]>([])

  // ========== 加载说说列表 ==========
  async function loadPosts(reset = false) {
    if (reset) {
      pageNum.value = 1
    }
    loading.value = true
    try {
      const userId = currentUser.value?.id
      const res = await getSpacePostPage({
        pageNum: pageNum.value,
        pageSize: pageSize.value,
        userId
      })
      posts.value = res.records.map((post) => ({
        ...post,
        liked: post.likeIds?.includes(currentUser.value?.id || 0) ?? false
      }))
      total.value = res.total
    } catch {
      posts.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  // ========== 加载统计数据 ==========
  async function loadStats() {
    const userId = currentUser.value?.id
    if (!userId) return
    try {
      const res = await get<{ postCount: number; likeCount: number }>('/space-posts/stats', { userId })
      stats.value = {
        postCount: res.postCount || 0,
        likeCount: res.likeCount || 0
      }
    } catch {
      // 静默失败，使用默认值
    }
  }

  // ========== 发表说说 ==========
  async function publishPost() {
    const content = publishContent.value.trim()
    if (!content && publishImages.value.length === 0) {
      ElMessage.warning('请输入内容或上传图片')
      return
    }
    if (content.length > 500) {
      ElMessage.warning('内容不能超过500字')
      return
    }

    isPublishing.value = true
    try {
      const dto: SpacePostDTO = {
        content: content || '',
        images: publishImages.value.length > 0 ? publishImages.value : undefined,
        isPrivate: false
      }

      // 根据实际文本内容过滤 mentions，只保留当前仍存在的 @用户名
      const actualMentions: number[] = []
      const mentionPattern = /@([^\s@,，.!?;:\[\]()]+)/g
      let m: RegExpExecArray | null
      while ((m = mentionPattern.exec(content)) !== null) {
        const key = '@' + m[1]
        if (mentionUserMap.value[key] !== undefined) {
          actualMentions.push(mentionUserMap.value[key])
        }
      }
      if (actualMentions.length > 0) {
        dto.extra = JSON.stringify({ mentions: actualMentions })
      }

      await addSpacePost(dto)
      ElMessage.success('发表成功')
      publishContent.value = ''
      publishImages.value = []
      mentionUserIds.value = []
      mentionUserMap.value = {}
      showPublishArea.value = false
      await loadPosts(true)
      await loadStats()
    } catch (e: any) {
      ElMessage.error(e?.message || '发表失败')
    } finally {
      isPublishing.value = false
    }
  }

  // ========== 点赞/取消点赞 ==========
  async function toggleLike(post: SpacePostVO) {
    const user = currentUser.value
    if (!user) {
      ElMessage.warning('请先登录')
      return
    }

    const liked = post.liked
    const origLikeCount = post.likeCount || 0
    const origLikeIds = post.likeIds ? [...post.likeIds] : []

    // 乐观更新
    post.liked = !liked
    if (post.liked) {
      post.likeCount = origLikeCount + 1
      post.likeIds = [...origLikeIds, user.id]
    } else {
      post.likeCount = Math.max(0, origLikeCount - 1)
      post.likeIds = origLikeIds.filter((id) => id !== user.id)
    }

    try {
      await likeSpacePost(post.id)
    } catch {
      // 回滚
      post.liked = liked
      post.likeCount = origLikeCount
      post.likeIds = origLikeIds
      ElMessage.error('操作失败')
    }
  }

  // ========== 转发 ==========
  function openForward(post: SpacePostVO) {
    forwardTarget.value = post
    forwardContent.value = ''
    showForwardDialog.value = true
  }

  async function submitForward() {
    if (!forwardTarget.value) return
    const content = forwardContent.value.trim()
    if (content.length > 500) {
      ElMessage.warning('转发文字不能超过500字')
      return
    }

    isForwarding.value = true
    try {
      const dto: SpacePostForwardDTO = {
        sourceId: forwardTarget.value.id,
        content
      }
      await forwardSpacePost(dto)
      ElMessage.success('转发成功')
      showForwardDialog.value = false
      forwardTarget.value = null
      forwardContent.value = ''
      await loadPosts(true)
      await loadStats()
    } catch (e: any) {
      ElMessage.error(e?.message || '转发失败')
    } finally {
      isForwarding.value = false
    }
  }

  // ========== 删除说说 ==========
  async function removePost(post: SpacePostVO) {
    try {
      await deleteSpacePost(post.id)
      ElMessage.success('删除成功')
      await loadPosts(true)
      await loadStats()
    } catch (e: any) {
      ElMessage.error(e?.message || '删除失败')
    }
  }

  // ========== 图片上传 ==========
  async function uploadImageAction(file: File): Promise<string | null> {
    if (publishImages.value.length >= 9) {
      ElMessage.warning('最多上传9张图片')
      return null
    }
    imageUploading.value = true
    try {
      const { postForm } = await import('@/utils/request')
      const fd = new FormData()
      fd.append('file', file)
      const url: string = await postForm('/space-posts/upload-image', fd)
      publishImages.value.push(url)
      return url
    } catch {
      ElMessage.error('图片上传失败')
      return null
    } finally {
      imageUploading.value = false
    }
  }

  function removeImage(index: number) {
    publishImages.value.splice(index, 1)
  }

  // ========== @提及 ==========
  async function searchMentionUsers() {
    if (!mentionKeyword.value.trim()) {
      mentionUsers.value = []
      return
    }
    mentionLoading.value = true
    try {
      const users = await get<UserVO[]>('/users/search', {
        keyword: mentionKeyword.value.trim(),
        limit: 10
      })
      mentionUsers.value = users || []
    } catch {
      mentionUsers.value = []
    } finally {
      mentionLoading.value = false
    }
  }

  function addMention(user: UserVO) {
    const mentionText = `@${user.name || user.username}`
    publishContent.value += mentionText + ' '
    if (user.id && !mentionUserIds.value.includes(user.id)) {
      mentionUserIds.value.push(user.id)
    }
    if (user.id) {
      mentionUserMap.value[mentionText] = user.id
    }
    showMentionDialog.value = false
    mentionKeyword.value = ''
    mentionUsers.value = []
  }

  // ========== 时间格式化 ==========
  function formatTime(time?: string): string {
    if (!time) return ''
    const date = new Date(time)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  // ========== 分页 ==========
  function handlePageChange(page: number) {
    pageNum.value = page
    loadPosts()
  }

  // ========== 初始化 ==========
  function init() {
    loadPosts(true)
    loadStats()
  }

  return {
    currentUser,
    posts,
    total,
    pageNum,
    pageSize,
    loading,
    stats,
    showPublishArea,
    publishContent,
    publishImages,
    isPublishing,
    imageUploading,
    showForwardDialog,
    forwardTarget,
    forwardContent,
    isForwarding,
    activeCommentPostId,
    showMentionDialog,
    mentionKeyword,
    mentionLoading,
    mentionUsers,
    loadPosts,
    loadStats,
    publishPost,
    toggleLike,
    openForward,
    submitForward,
    removePost,
    uploadImageAction,
    removeImage,
    searchMentionUsers,
    addMention,
    formatTime,
    handlePageChange,
    init
  }
}
