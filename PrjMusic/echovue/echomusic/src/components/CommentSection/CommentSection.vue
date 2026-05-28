<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound, CaretBottom } from '@element-plus/icons-vue'
import { getCommentPage, addComment, likeComment, dislikeComment } from '@/api/comment'
import type { CommentVO, CommentDTO, CommentPageQuery } from '@/types/comment'
import { getUser } from '@/utils/authStorage'

const props = defineProps<{
  sceneType: string
  sceneId: number
}>()

const currentUser = computed(() => getUser())

// ========== 主评论 ==========
const comments = ref<CommentVO[]>([])
const commentTotal = ref(0)
const commentPageNum = ref(1)
const commentPageSize = ref(10)
const commentLoading = ref(false)

// ========== 发表评论 ==========
const commentContent = ref('')
const commentSubmitting = ref(false)

// ========== 回复 ==========
const replyingToId = ref<number | null>(null)   // 当前正在回复的评论ID
const replyingToName = ref('')                  // 被回复者名称
const replyParentId = ref<number | null>(null)  // 所属主评论ID（用于嵌套回复）
const replyContent = ref('')
const replySubmitting = ref(false)

// ========== 回复列表 ==========
interface ReplyState {
  list: CommentVO[]
  total: number
  pageNum: number
  pageSize: number
  loading: boolean
  expanded: boolean
}
const repliesMap = ref<Map<number, ReplyState>>(new Map())

// ========== 展开/收起 ==========
const expanded = ref(false)

// ========== 点赞/点踩 loading ==========
const likeLoadingIds = ref<Set<number>>(new Set())
const dislikeLoadingIds = ref<Set<number>>(new Set())

// ========== 加载主评论 ==========
async function loadComments() {
  commentLoading.value = true
  try {
    const params: CommentPageQuery = {
      pageNum: commentPageNum.value,
      pageSize: commentPageSize.value,
      sceneType: props.sceneType,
      sceneId: props.sceneId,
      isReply: false,
      sortBy: 'create_time',
      sortOrder: 'desc'
    }
    const res = await getCommentPage(params)
    comments.value = res.records
    commentTotal.value = res.total
  } catch {
    comments.value = []
    commentTotal.value = 0
  } finally {
    commentLoading.value = false
  }
}

// ========== 发表评论 ==========
async function submitComment() {
  const content = commentContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入评论内容')
    return
  }
  const user = currentUser.value
  if (!user) {
    ElMessage.warning('请先登录')
    return
  }

  commentSubmitting.value = true
  try {
    await addComment({
      sceneType: props.sceneType,
      sceneId: props.sceneId,
      content,
      userId: user.id,
      userName: user.name || user.username || '匿名用户'
    })
    ElMessage.success('评论发表成功')
    commentContent.value = ''
    commentPageNum.value = 1
    await loadComments()
  } catch (e: any) {
    ElMessage.error(e?.message || '评论发表失败')
  } finally {
    commentSubmitting.value = false
  }
}

// ========== 回复相关 ==========
function startReply(target: CommentVO, parentId: number) {
  // 如果已经在回复同一条，则关闭
  if (replyingToId.value === target.id) {
    cancelReply()
    return
  }
  replyingToId.value = target.id
  replyingToName.value = target.userName || '匿名用户'
  replyParentId.value = parentId
  replyContent.value = ''
}

function cancelReply() {
  replyingToId.value = null
  replyingToName.value = ''
  replyParentId.value = null
  replyContent.value = ''
}

async function submitReply() {
  const content = replyContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入回复内容')
    return
  }
  const user = currentUser.value
  if (!user) {
    ElMessage.warning('请先登录')
    return
  }

  const targetId = replyingToId.value
  const parentId = replyParentId.value
  if (!targetId || !parentId) return

  const targetComment = findCommentById(targetId)
  if (!targetComment) return

  replySubmitting.value = true
  try {
    const dto: CommentDTO = {
      sceneType: props.sceneType,
      sceneId: props.sceneId,
      content,
      userId: user.id,
      userName: user.name || user.username || '匿名用户',
      isReply: true,
      replyCommentId: parentId,
      replyUserId: targetComment.userId
    }

    // 嵌套回复
    if (targetComment.isReply) {
      dto.isNestedReply = true
      dto.nestedReplyCommentId = targetComment.id
      dto.nestedReplyUserId = targetComment.userId
    }

    await addComment(dto)
    ElMessage.success('回复成功')
    cancelReply()

    // 刷新该主评论的回复列表
    const state = repliesMap.value.get(parentId)
    if (state && state.expanded) {
      await loadReplies(parentId, 1)
    } else {
      // 如果未展开，展开并加载
      await toggleReplies(parentId)
    }

    // 更新主评论的 answerCount
    const mainComment = comments.value.find(c => c.id === parentId)
    if (mainComment) {
      mainComment.answerCount = (mainComment.answerCount ?? 0) + 1
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '回复失败')
  } finally {
    replySubmitting.value = false
  }
}

function findCommentById(id: number): CommentVO | undefined {
  // 先在主评论中找
  let found = comments.value.find(c => c.id === id)
  if (found) return found
  // 再在回复中找
  for (const state of repliesMap.value.values()) {
    found = state.list.find(c => c.id === id)
    if (found) return found
  }
  return undefined
}

// ========== 回复列表 ==========
async function loadReplies(mainCommentId: number, page: number) {
  let state = repliesMap.value.get(mainCommentId)
  if (!state) {
    state = {
      list: [],
      total: 0,
      pageNum: 1,
      pageSize: 10,
      loading: false,
      expanded: false
    }
    repliesMap.value.set(mainCommentId, state)
  }

  state.loading = true
  try {
    const res = await getCommentPage({
      pageNum: page,
      pageSize: state.pageSize,
      sceneType: props.sceneType,
      sceneId: props.sceneId,
      replyCommentId: mainCommentId,
      sortBy: 'create_time',
      sortOrder: 'asc'
    })
    state.list = res.records
    state.total = res.total
    state.pageNum = page
  } catch {
    state.list = []
    state.total = 0
  } finally {
    state.loading = false
  }
}

async function toggleReplies(mainCommentId: number) {
  const state = repliesMap.value.get(mainCommentId)
  if (state && state.expanded) {
    state.expanded = false
    return
  }
  await loadReplies(mainCommentId, 1)
  const newState = repliesMap.value.get(mainCommentId)
  if (newState) newState.expanded = true
}

// ========== 点赞/点踩 ==========
function isLiked(comment: CommentVO): boolean {
  const userId = currentUser.value?.id
  if (!userId || !comment.likeIds) return false
  return comment.likeIds.includes(userId)
}

function isDisliked(comment: CommentVO): boolean {
  const userId = currentUser.value?.id
  if (!userId || !comment.dislikeIds) return false
  return comment.dislikeIds.includes(userId)
}

async function handleLike(comment: CommentVO) {
  const user = currentUser.value
  if (!user) {
    ElMessage.warning('请先登录')
    return
  }
  if (likeLoadingIds.value.has(comment.id)) return

  const liked = isLiked(comment)
  const hadDisliked = isDisliked(comment)
  // 保存原始值用于回滚
  const origLikeCount = comment.likeCount ?? 0
  const origDislikeCount = comment.dislikeCount ?? 0
  const origLikeIds = comment.likeIds ? [...comment.likeIds] : []
  const origDislikeIds = comment.dislikeIds ? [...comment.dislikeIds] : []

  likeLoadingIds.value.add(comment.id)

  // 乐观更新
  if (!comment.likeIds) comment.likeIds = []
  if (!comment.dislikeIds) comment.dislikeIds = []
  if (liked) {
    // 取消点赞
    comment.likeIds = comment.likeIds.filter(id => id !== user.id)
    comment.likeCount = Math.max(0, origLikeCount - 1)
  } else {
    // 点赞（同时取消点踩）
    comment.likeIds.push(user.id)
    comment.dislikeIds = comment.dislikeIds.filter(id => id !== user.id)
    comment.likeCount = origLikeCount + 1
    comment.dislikeCount = Math.max(0, origDislikeCount - 1)
  }

  try {
    await likeComment(comment.id)
  } catch {
    // 回滚到原始值
    comment.likeIds = origLikeIds
    comment.dislikeIds = origDislikeIds
    comment.likeCount = origLikeCount
    comment.dislikeCount = origDislikeCount
    ElMessage.error('操作失败')
  } finally {
    likeLoadingIds.value.delete(comment.id)
  }
}

async function handleDislike(comment: CommentVO) {
  const user = currentUser.value
  if (!user) {
    ElMessage.warning('请先登录')
    return
  }
  if (dislikeLoadingIds.value.has(comment.id)) return

  const disliked = isDisliked(comment)
  const hadLiked = isLiked(comment)
  // 保存原始值用于回滚
  const origLikeCount = comment.likeCount ?? 0
  const origDislikeCount = comment.dislikeCount ?? 0
  const origLikeIds = comment.likeIds ? [...comment.likeIds] : []
  const origDislikeIds = comment.dislikeIds ? [...comment.dislikeIds] : []

  dislikeLoadingIds.value.add(comment.id)

  // 乐观更新
  if (!comment.likeIds) comment.likeIds = []
  if (!comment.dislikeIds) comment.dislikeIds = []
  if (disliked) {
    // 取消点踩
    comment.dislikeIds = comment.dislikeIds.filter(id => id !== user.id)
    comment.dislikeCount = Math.max(0, origDislikeCount - 1)
  } else {
    // 点踩（同时取消点赞）
    comment.dislikeIds.push(user.id)
    comment.likeIds = comment.likeIds.filter(id => id !== user.id)
    comment.dislikeCount = origDislikeCount + 1
    comment.likeCount = Math.max(0, origLikeCount - 1)
  }

  try {
    await dislikeComment(comment.id)
  } catch {
    // 回滚到原始值
    comment.likeIds = origLikeIds
    comment.dislikeIds = origDislikeIds
    comment.likeCount = origLikeCount
    comment.dislikeCount = origDislikeCount
    ElMessage.error('操作失败')
  } finally {
    dislikeLoadingIds.value.delete(comment.id)
  }
}

// ========== 分页 ==========
function handlePageChange(page: number) {
  commentPageNum.value = page
  loadComments()
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

// ========== 监听场景变化 ==========
watch(() => [props.sceneType, props.sceneId], () => {
  commentPageNum.value = 1
  commentContent.value = ''
  repliesMap.value.clear()
  cancelReply()
  loadComments()
}, { immediate: true })
</script>

<template>
  <div class="comment-section-root">
    <!-- 评论区头部 -->
    <div class="comment-header" @click="expanded = !expanded">
      <div class="comment-header-left">
        <span>评论</span>
        <span class="comment-count">{{ commentTotal }} 条</span>
      </div>
      <el-icon class="expand-icon" :class="{ expanded }"><CaretBottom /></el-icon>
    </div>

    <div v-if="expanded" class="comment-section-body">
      <!-- 评论输入框 -->
      <div class="comment-form-box">
      <div class="comment-form-header">
        <el-avatar :size="40" :src="undefined" class="comment-form-avatar">
          {{ currentUser?.name?.charAt(0) || currentUser?.username?.charAt(0) || '?' }}
        </el-avatar>
        <el-input
          v-model="commentContent"
          type="textarea"
          :rows="3"
          placeholder="发一条友善的评论吧~"
          maxlength="500"
          show-word-limit
          resize="none"
          class="comment-form-input"
        />
      </div>
      <div class="comment-form-actions">
        <el-button
          type="primary"
          :loading="commentSubmitting"
          @click="submitComment"
        >
          发表评论
        </el-button>
      </div>
    </div>

    <!-- 排序 tab（占位，默认最新） -->
    <div class="comment-sort-bar">
      <span class="sort-item active">最新</span>
    </div>

    <!-- 评论列表 -->
    <div v-loading="commentLoading" class="comment-list">
      <!-- 主评论项 -->
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="main-comment"
      >
        <!-- 主评论头部 -->
        <div class="comment-row">
          <el-avatar :size="40" :src="undefined" class="comment-avatar">
            {{ comment.userName?.charAt(0) || '?' }}
          </el-avatar>
          <div class="comment-body">
            <div class="comment-meta">
              <span class="comment-username">{{ comment.userName || '匿名用户' }}</span>
              <span class="comment-time">{{ formatTime(comment.createTime) }}</span>
            </div>
            <div class="comment-text">{{ comment.content }}</div>

            <!-- 操作栏 -->
            <div class="comment-actions">
              <button
                class="action-btn"
                :class="{ active: isLiked(comment) }"
                :disabled="likeLoadingIds.has(comment.id)"
                @click="handleLike(comment)"
              >
                <svg class="icon-svg" :class="{ active: isLiked(comment) }" viewBox="0 0 24 24" width="16" height="16">
                  <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>{{ comment.likeCount ?? 0 }}</span>
              </button>
              <button
                class="action-btn"
                :class="{ active: isDisliked(comment) }"
                :disabled="dislikeLoadingIds.has(comment.id)"
                @click="handleDislike(comment)"
              >
                <svg class="icon-svg" :class="{ active: isDisliked(comment) }" viewBox="0 0 24 24" width="16" height="16">
                  <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span>{{ comment.dislikeCount ?? 0 }}</span>
              </button>
              <button class="action-btn" @click="startReply(comment, comment.id)">
                <el-icon><ChatDotRound /></el-icon>
                <span>回复</span>
              </button>
            </div>

            <!-- 回复输入框 -->
            <div v-if="replyingToId === comment.id" class="reply-input-box">
              <el-input
                v-model="replyContent"
                type="textarea"
                :rows="2"
                :placeholder="`回复 ${replyingToName}...`"
                maxlength="500"
                show-word-limit
                resize="none"
              />
              <div class="reply-input-actions">
                <el-button size="small" @click="cancelReply">取消</el-button>
                <el-button
                  size="small"
                  type="primary"
                  :loading="replySubmitting"
                  @click="submitReply"
                >
                  发送回复
                </el-button>
              </div>
            </div>

            <!-- 回复列表触发 -->
            <div v-if="comment.answerCount" class="reply-trigger">
              <button
                class="reply-trigger-btn"
                @click="toggleReplies(comment.id)"
              >
                <el-icon class="trigger-icon" :class="{ expanded: repliesMap.get(comment.id)?.expanded }">
                  <CaretBottom />
                </el-icon>
                <span>{{ comment.answerCount }} 条回复</span>
              </button>
            </div>

            <!-- 回复列表 -->
            <div
              v-if="repliesMap.get(comment.id)?.expanded"
              v-loading="repliesMap.get(comment.id)?.loading"
              class="reply-list"
            >
              <div
                v-for="reply in repliesMap.get(comment.id)?.list"
                :key="reply.id"
                class="reply-item"
              >
                <el-avatar :size="32" :src="undefined" class="reply-avatar">
                  {{ reply.userName?.charAt(0) || '?' }}
                </el-avatar>
                <div class="reply-body">
                  <div class="reply-meta">
                    <span class="reply-username">{{ reply.userName || '匿名用户' }}</span>
                    <span class="reply-time">{{ formatTime(reply.createTime) }}</span>
                  </div>
                  <div class="reply-text">
                    <template v-if="reply.isNestedReply && reply.nestedReplyUserId">
                      <span class="reply-at">回复 <span class="reply-at-name">{{ findCommentById(reply.nestedReplyCommentId || 0)?.userName || '某人' }}</span>：</span>
                    </template>
                    {{ reply.content }}
                  </div>
                  <div class="reply-actions">
                    <button
                      class="action-btn small"
                      :class="{ active: isLiked(reply) }"
                      :disabled="likeLoadingIds.has(reply.id)"
                      @click="handleLike(reply)"
                    >
                      <svg class="icon-svg" :class="{ active: isLiked(reply) }" viewBox="0 0 24 24" width="14" height="14">
                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>{{ reply.likeCount ?? 0 }}</span>
                    </button>
                    <button
                      class="action-btn small"
                      :class="{ active: isDisliked(reply) }"
                      :disabled="dislikeLoadingIds.has(reply.id)"
                      @click="handleDislike(reply)"
                    >
                      <svg class="icon-svg" :class="{ active: isDisliked(reply) }" viewBox="0 0 24 24" width="14" height="14">
                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>{{ reply.dislikeCount ?? 0 }}</span>
                    </button>
                    <button class="action-btn small" @click="startReply(reply, comment.id)">
                      <span>回复</span>
                    </button>
                  </div>

                  <!-- 嵌套回复输入框 -->
                  <div v-if="replyingToId === reply.id" class="reply-input-box nested">
                    <el-input
                      v-model="replyContent"
                      type="textarea"
                      :rows="2"
                      :placeholder="`回复 ${replyingToName}...`"
                      maxlength="500"
                      show-word-limit
                      resize="none"
                    />
                    <div class="reply-input-actions">
                      <el-button size="small" @click="cancelReply">取消</el-button>
                      <el-button
                        size="small"
                        type="primary"
                        :loading="replySubmitting"
                        @click="submitReply"
                      >
                        发送回复
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 回复分页 -->
              <div
                v-if="(repliesMap.get(comment.id)?.total || 0) > (repliesMap.get(comment.id)?.pageSize || 10)"
                class="reply-pagination"
              >
                <el-pagination
                  :current-page="repliesMap.get(comment.id)?.pageNum"
                  :page-size="repliesMap.get(comment.id)?.pageSize"
                  :total="repliesMap.get(comment.id)?.total"
                  layout="prev, pager, next"
                  small
                  @change="(page: number) => loadReplies(comment.id, page)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="comments.length === 0 && !commentLoading" class="comment-empty">
        <p>暂无评论，快来抢沙发吧~</p>
      </div>
    </div>

    <!-- 主评论分页 -->
    <div v-if="commentTotal > commentPageSize" class="comment-pagination">
      <el-pagination
        v-model:current-page="commentPageNum"
        :page-size="commentPageSize"
        :total="commentTotal"
        layout="prev, pager, next"
        @change="handlePageChange"
      />
    </div>
    </div>
  </div>
</template>

<style scoped src="./CommentSection.css"></style>
