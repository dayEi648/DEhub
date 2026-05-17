<template>
  <div class="comment-section">
    <div v-if="!isExpanded" class="comment-collapsed" @click="expandComments">
      <span class="comment-count-text">💬 评论 {{ commentStore.totalComments }}</span>
      <span class="expand-hint">点击展开</span>
    </div>

    <template v-else>
      <div class="comment-header">
        <h3>评论 <span class="comment-count">{{ commentStore.totalComments }}</span></h3>
        <div class="sort-tabs">
          <button
            v-for="tab in sortTabs"
            :key="tab.value"
            class="sort-tab"
            :class="{ active: currentSort === tab.value }"
            @click="currentSort = tab.value"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div class="comment-input-area">
        <textarea
          v-model="newComment"
          class="comment-textarea"
          placeholder="写下你的评论..."
          rows="3"
        />
        <div class="comment-actions">
          <PrimaryButton @click="submitComment">发送</PrimaryButton>
        </div>
      </div>

      <div class="comment-list">
        <CommentItem
          v-for="comment in rootComments"
          :key="comment.id"
          :comment="comment"
          :target-type="targetType"
          :target-id="targetId"
          :root-id="comment.id"
          :depth="0"
          :replies="getReplies(comment.id)"
          :replies-loaded="loadedRootIds.has(comment.id)"
          @load-replies="loadReplies"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useCommentStore } from '@/stores/comment'
import PrimaryButton from './PrimaryButton.vue'
import CommentItem from './CommentItem.vue'

interface Props {
  targetType: string
  targetId: number
}
const props = defineProps<Props>()

const commentStore = useCommentStore()
const newComment = ref('')
const currentSort = ref<'time' | 'hot'>('time')
const isExpanded = ref(false)
const loadedRootIds = ref<Set<number>>(new Set())

const sortTabs = [
  { label: '最新', value: 'time' as const },
  { label: '热门', value: 'hot' as const }
]

const rootComments = computed(() => {
  return commentStore.comments.filter((c) => c.parent_id === null)
})

function getReplies(parentId: number) {
  return commentStore.comments.filter((c) => c.parent_id === parentId)
}

async function expandComments() {
  isExpanded.value = true
  await loadRootComments()
}

async function loadRootComments() {
  const data = await commentStore.fetchComments({
    target_type: props.targetType,
    target_id: props.targetId,
    parent_id: null,
    sort_by: currentSort.value,
    skip: 0,
    limit: 20
  })
  commentStore.totalComments = data.total
}

async function loadReplies(rootId: number) {
  if (loadedRootIds.value.has(rootId)) return
  await commentStore.fetchComments({
    target_type: props.targetType,
    target_id: props.targetId,
    parent_id: rootId,
    sort_by: currentSort.value,
    skip: 0,
    limit: 100
  }, true)
  loadedRootIds.value.add(rootId)
}

async function submitComment() {
  if (!newComment.value.trim()) return
  await commentStore.createComment({
    target_type: props.targetType,
    target_id: props.targetId,
    content: newComment.value.trim()
  })
  newComment.value = ''
}

watch(currentSort, () => {
  loadedRootIds.value.clear()
  if (isExpanded.value) {
    loadRootComments()
  }
})
</script>

<style scoped>
.comment-section {
  padding: 40px 0;
}
.comment-collapsed {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: var(--button-default-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background 0.2s;
}
.comment-collapsed:hover {
  background: rgba(0, 0, 0, 0.06);
}
.comment-count-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}
.expand-hint {
  font-size: 13px;
  color: var(--text-tertiary);
}
.comment-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.comment-header h3 {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  color: var(--text-primary);
}
.comment-count {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-left: 8px;
}
.sort-tabs {
  display: flex;
  gap: 8px;
}
.sort-tab {
  padding: 4px 12px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.2s;
}
.sort-tab.active {
  background: var(--text-primary);
  color: var(--text-white);
}
.comment-input-area {
  margin-bottom: 32px;
}
.comment-textarea {
  width: 100%;
  padding: 12px 16px;
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  resize: vertical;
  outline: none;
}
.comment-textarea:focus {
  border-color: var(--apple-blue);
}
.comment-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
