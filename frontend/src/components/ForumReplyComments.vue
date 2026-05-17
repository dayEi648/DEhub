<template>
  <div class="reply-comments">
    <div v-if="!loaded" class="loading-hint">
      <button class="action-link" @click="loadAll">加载评论</button>
    </div>
    <template v-else>
      <div v-if="secondLayer.length > 0" class="comments-list">
        <div
          v-for="comment in secondLayer"
          :key="comment.id"
          class="comment-item-small"
        >
          <Avatar :size="24" :src="comment.user.avatar_url" :name="comment.user.username" />
          <div class="comment-body-small">
            <div class="comment-meta-small">
              <span class="comment-author-small">{{ comment.user.username }}</span>
              <span class="comment-time-small">{{ formatTime(comment.created_at) }}</span>
            </div>
            <span class="comment-content-small">{{ comment.content }}</span>
            <button class="reply-link-small" @click="toggleReplyInput(comment.id)">回复</button>

            <!-- 回复输入框 -->
            <div v-if="activeReplyId === comment.id" class="reply-input-wrap">
              <textarea
                v-model="replyInputs[comment.id]"
                class="comment-textarea-small"
                rows="2"
                :placeholder="`回复 @${comment.user.username} `"
              />
              <div class="comment-actions-small">
                <button class="submit-btn-small" @click="submitReply(comment)">发送</button>
              </div>
            </div>

            <!-- 第三层评论 -->
            <div v-if="thirdLayer[comment.id]?.length > 0" class="third-layer-list">
              <div
                v-for="reply in thirdLayer[comment.id]"
                :key="reply.id"
                class="third-layer-item"
              >
                <span class="comment-author-small">{{ reply.user.username }}</span>
                <span class="comment-content-small">{{ reply.content }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-comments">暂无回复</div>

      <div class="comment-input-area-small">
        <textarea
          v-model="newContent"
          class="comment-textarea-small"
          rows="2"
          placeholder="写下你的评论..."
        />
        <div class="comment-actions-small">
          <button class="submit-btn-small" @click="submitNew">发送</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { CommentResponse } from '@/types'
import * as commentApi from '@/api/comment'
import Avatar from './Avatar.vue'

interface Props {
  replyId: number
}
const props = defineProps<Props>()

const loaded = ref(false)
const comments = ref<CommentResponse[]>([])
const newContent = ref('')
const activeReplyId = ref<number | null>(null)
const replyInputs = reactive<Record<number, string>>({})

const secondLayer = ref<CommentResponse[]>([])
const thirdLayer = reactive<Record<number, CommentResponse[]>>({})

async function loadAll() {
  try {
    // 加载第二层（直接回复 ForumReply）
    const { data: secondData } = await commentApi.fetchComments({
      target_type: 'forum_reply',
      target_id: props.replyId,
      sort_by: 'time',
      skip: 0,
      limit: 100
    })
    secondLayer.value = secondData.items

    // 为每个第二层加载第三层（回复第二层）
    for (const comment of secondLayer.value) {
      const { data: thirdData } = await commentApi.fetchComments({
        target_type: 'comment',
        target_id: comment.id,
        sort_by: 'time',
        skip: 0,
        limit: 100
      })
      thirdLayer[comment.id] = thirdData.items
    }

    loaded.value = true
  } catch (e) {
    console.error('加载评论失败', e)
  }
}

async function submitNew() {
  if (!newContent.value.trim()) return
  try {
    const { data: comment } = await commentApi.createComment({
      target_type: 'forum_reply',
      target_id: props.replyId,
      content: newContent.value.trim()
    })
    secondLayer.value.push(comment)
    newContent.value = ''
  } catch (e) {
    console.error('发送评论失败', e)
  }
}

function toggleReplyInput(commentId: number) {
  activeReplyId.value = activeReplyId.value === commentId ? null : commentId
}

async function submitReply(parentComment: CommentResponse) {
  const content = replyInputs[parentComment.id]?.trim()
  if (!content) return
  try {
    const { data: comment } = await commentApi.createComment({
      target_type: 'comment',
      target_id: parentComment.id,
      parent_id: parentComment.id,
      content: `@${parentComment.user.username} ${content}`
    })
    if (!thirdLayer[parentComment.id]) {
      thirdLayer[parentComment.id] = []
    }
    thirdLayer[parentComment.id].push(comment)
    replyInputs[parentComment.id] = ''
    activeReplyId.value = null
  } catch (e) {
    console.error('发送回复失败', e)
  }
}

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}
</script>

<style scoped>
.reply-comments {
  margin-top: 12px;
  padding-left: 44px;
}
.loading-hint {
  padding: 8px 0;
}
.no-comments {
  font-size: 13px;
  color: var(--text-tertiary);
  padding: 8px 0;
}
.comments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
.comment-item-small {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.comment-body-small {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.comment-meta-small {
  display: flex;
  gap: 8px;
  align-items: center;
}
.comment-author-small {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}
.comment-content-small {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.comment-time-small {
  font-size: 11px;
  color: var(--text-tertiary);
}
.reply-link-small {
  font-size: 12px;
  color: var(--link-blue);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  align-self: flex-start;
}
.reply-input-wrap {
  margin-top: 4px;
}
.third-layer-list {
  margin-top: 4px;
  padding-left: 12px;
  border-left: 2px solid rgba(0, 0, 0, 0.06);
}
.third-layer-item {
  display: flex;
  gap: 4px;
  align-items: baseline;
  padding: 4px 0;
  font-size: 12px;
}
.comment-input-area-small {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.comment-textarea-small {
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  background: var(--button-default-light);
  border: 2px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  resize: vertical;
  outline: none;
}
.comment-textarea-small:focus {
  border-color: var(--apple-blue);
}
.comment-actions-small {
  display: flex;
  justify-content: flex-end;
}
.submit-btn-small {
  padding: 4px 12px;
  font-size: 12px;
  color: var(--text-white);
  background: var(--text-primary);
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
}
.action-link {
  font-size: 12px;
  color: var(--link-blue);
  background: transparent;
  border: none;
  cursor: pointer;
}
</style>
