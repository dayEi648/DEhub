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
        <textarea v-model="replyContent" class="reply-textarea" rows="2" placeholder="回复..." />
        <div class="reply-actions">
          <PrimaryButton @click="submitReply">发送</PrimaryButton>
        </div>
      </div>
      <!-- 嵌套子评论 -->
      <div v-if="replies.length > 0" class="replies-list">
        <CommentItem
          v-for="reply in replies"
          :key="reply.id"
          :comment="reply"
          :target-type="targetType"
          :target-id="targetId"
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
  depth?: number
  replies?: CommentResponse[]
}
const props = withDefaults(defineProps<Props>(), {
  depth: 0,
  replies: () => []
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
  await commentStore.createComment({
    target_type: props.targetType,
    target_id: props.targetId,
    parent_id: props.comment.id,
    content: replyContent.value.trim()
  })
  replyContent.value = ''
  showReply.value = false
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
</style>
