<template>
  <div class="comment-item" :style="indentStyle">
    <Avatar :src="comment.user.avatar_url" :name="comment.user.username" :size="32" />
    <div class="comment-body">
      <div class="comment-meta">
        <span class="comment-author">{{ comment.user.username }}</span>
        <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
      </div>
      <p class="comment-content">{{ comment.content }}</p>
      <div class="comment-actions">
        <button class="action-btn" @click="toggleLike">
          <span class="heart-icon" :class="{ liked: isLiked }">♥</span>
          {{ comment.likecount }}
        </button>
        <button class="action-btn" @click="showReply = !showReply">回复</button>
        <button v-if="canDelete" class="action-btn delete" @click="deleteComment">删除</button>
      </div>
      <div v-if="showReply" class="reply-input-area">
        <textarea v-model="replyContent" class="reply-textarea" rows="2" :placeholder="replyPlaceholder" />
        <div class="reply-actions">
          <PrimaryButton @click="submitReply">发送</PrimaryButton>
        </div>
      </div>

      <!-- 查看所有回复按钮（仅表层评论显示） -->
      <div v-if="depth === 0 && !repliesLoaded" class="load-replies-btn">
        <button class="action-btn" @click="emitLoadReplies">
          查看所有回复
        </button>
      </div>

      <!-- 嵌套子评论 -->
      <div v-if="replies.length > 0 && depth === 0" class="replies-list">
        <CommentItem
          v-for="reply in replies"
          :key="reply.id"
          :comment="reply"
          :target-type="targetType"
          :target-id="targetId"
          :root-id="rootId"
          :depth="depth + 1"
          :replies="[]"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useCommentStore } from '@/stores/comment'
import { useAuthStore } from '@/stores/auth'
import type { CommentResponse } from '@/types'
import Avatar from './Avatar.vue'
import PrimaryButton from './PrimaryButton.vue'

interface Props {
  comment: CommentResponse
  targetType: string
  targetId: number
  rootId: number
  depth?: number
  replies?: CommentResponse[]
  repliesLoaded?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  depth: 0,
  replies: () => [],
  repliesLoaded: false
})

const emit = defineEmits<{
  loadReplies: [rootId: number]
}>()

const replyPlaceholder = computed(() => {
  return props.depth === 0 ? '回复...' : `回复 @${props.comment.user.username} `
})

const commentStore = useCommentStore()
const authStore = useAuthStore()
const showReply = ref(false)
const replyContent = ref('')

const indentStyle = computed(() => ({
  paddingLeft: props.depth > 0 ? `${props.depth * 48}px` : '0'
}))

const isLiked = computed(() => commentStore.likedCommentIds.has(props.comment.id))

const canDelete = computed(() => {
  return authStore.user?.id === props.comment.user_id || authStore.isAdmin
})

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

async function toggleLike() {
  await commentStore.toggleLike(props.comment.id)
}

async function deleteComment() {
  await commentStore.deleteComment(props.comment.id)
}

async function submitReply() {
  if (!replyContent.value.trim()) return
  const isReplyToInner = props.depth === 1
  const content = isReplyToInner
    ? `@${props.comment.user.username} ${replyContent.value.trim()}`
    : replyContent.value.trim()
  await commentStore.createComment({
    target_type: isReplyToInner ? 'comment' : props.targetType,
    target_id: isReplyToInner ? props.comment.id : props.targetId,
    parent_id: props.rootId,
    content
  })
  replyContent.value = ''
  showReply.value = false
}

function emitLoadReplies() {
  emit('loadReplies', props.comment.id)
}
</script>

<style scoped>
.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.comment-body {
  flex: 1;
}
.comment-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.comment-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.comment-time {
  font-size: 12px;
  color: var(--text-tertiary);
}
.comment-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.comment-actions {
  display: flex;
  gap: 16px;
}
.action-btn {
  font-size: 12px;
  color: var(--text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.2s;
}
.action-btn:hover {
  color: var(--text-secondary);
}
.action-btn.delete:hover {
  color: var(--error-red);
}
.heart-icon {
  transition: transform 0.15s;
}
.heart-icon.liked {
  color: var(--error-red);
}
.action-btn:active .heart-icon {
  transform: scale(1.3);
}
.reply-input-area {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.reply-textarea {
  width: 100%;
  padding: 8px 12px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  resize: vertical;
  outline: none;
}
.reply-textarea:focus {
  border-color: var(--apple-blue);
}
.reply-actions {
  display: flex;
  justify-content: flex-end;
}
.replies-list {
  margin-top: 8px;
}
.load-replies-btn {
  margin-top: 8px;
}
</style>
