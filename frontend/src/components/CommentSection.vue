<template>
  <div class="comment-section">
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
        :depth="0"
        :replies="getReplies(comment.id)"
      />
    </div>
    <!-- 滚动加载触发元素 -->
    <div v-if="hasMore" ref="loadTriggerRef" class="load-trigger">
      <LoadingSpinner v-if="loadingMore" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useCommentStore } from '@/stores/comment'
import PrimaryButton from './PrimaryButton.vue'
import CommentItem from './CommentItem.vue'
import LoadingSpinner from './LoadingSpinner.vue'

interface Props {
  targetType: string
  targetId: number
}
const props = defineProps<Props>()

const commentStore = useCommentStore()
const newComment = ref('')
const currentSort = ref<'time' | 'hot'>('time')
const currentSkip = ref(0)
const limit = 20
const loadingMore = ref(false)
const loadTriggerRef = ref<HTMLDivElement | null>(null)
let observer: IntersectionObserver | null = null

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

const hasMore = computed(() => {
  return commentStore.totalComments > commentStore.comments.length
})

async function loadComments(append = false) {
  if (loadingMore.value) return
  loadingMore.value = true
  try {
    const data = await commentStore.fetchComments({
      target_type: props.targetType,
      target_id: props.targetId,
      sort_by: currentSort.value,
      skip: append ? currentSkip.value : 0,
      limit
    })
    if (!append) {
      currentSkip.value = data.items.length
    } else {
      currentSkip.value += data.items.length
    }
  } finally {
    loadingMore.value = false
  }
}

async function loadMore() {
  await loadComments(true)
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

function setupObserver() {
  if (!loadTriggerRef.value) return
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && hasMore.value && !loadingMore.value) {
        loadMore()
      }
    },
    { rootMargin: '200px' }
  )
  observer.observe(loadTriggerRef.value)
}

onMounted(() => {
  loadComments()
  setupObserver()
})

onUnmounted(() => {
  observer?.disconnect()
})

watch(currentSort, () => loadComments(false))
</script>

<style scoped>
.comment-section {
  padding: 40px 0;
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
.load-trigger {
  display: flex;
  justify-content: center;
  padding: 24px 0;
  min-height: 48px;
}
</style>
