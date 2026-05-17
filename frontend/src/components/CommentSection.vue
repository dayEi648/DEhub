<template>
  <div class="comment-section">
    <div v-if="!isExpanded" class="comment-collapsed" @click="expandComments">
      <span class="comment-count-text">💬 评论 {{ displayTotal }}</span>
      <span class="expand-hint">点击展开</span>
    </div>

    <template v-else>
      <div class="comment-header">
        <h3>评论 <span class="comment-count">{{ displayTotal }}</span></h3>
        <div class="header-right">
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
          <button class="collapse-btn" @click="isExpanded = false">收起</button>
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
          :replies-loaded="loadedRootIds.has(comment.id)"
          :all-comments="commentStore.comments"
          @load-replies="loadReplies"
          @collapse-replies="collapseReplies"
        />
      </div>

      <Pagination
        v-if="commentStore.totalComments > pageSize"
        v-model:current-page="currentPage"
        :total="commentStore.totalComments"
        :page-size="pageSize"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useCommentStore } from '@/stores/comment'
import { useUiStore } from '@/stores/ui'
import PrimaryButton from './PrimaryButton.vue'
import CommentItem from './CommentItem.vue'
import Pagination from './Pagination.vue'

interface Props {
  targetType: string
  targetId: number
  totalCount?: number
}
const props = withDefaults(defineProps<Props>(), {
  totalCount: 0
})

const commentStore = useCommentStore()
const uiStore = useUiStore()
const newComment = ref('')
const currentSort = ref<'time' | 'hot'>('time')
const isExpanded = ref(false)
const loadedRootIds = ref<Set<number>>(new Set())
const currentPage = ref(1)
const pageSize = 10

const sortTabs = [
  { label: '最新', value: 'time' as const },
  { label: '热门', value: 'hot' as const }
]

const displayTotal = computed(() => {
  // 优先使用外部传入的 totalCount（如 blogPost.comment_count）
  // 若未传入则回退到 store 中当前查询返回的 total
  return props.totalCount || commentStore.totalComments
})

const rootComments = computed(() => {
  return commentStore.comments.filter((c) => c.parent_id === null)
})

function resetAndLoad() {
  commentStore.comments = []
  commentStore.totalComments = 0
  loadedRootIds.value.clear()
  currentPage.value = 1
}

async function expandComments() {
  isExpanded.value = true
  await loadRootComments()
}

async function loadRootComments() {
  try {
    const data = await commentStore.fetchComments({
      target_type: props.targetType,
      target_id: props.targetId,
      parent_id: null,
      sort_by: currentSort.value,
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize
    })
    // 保存接口返回的表层评论总数，用于分页
    commentStore.totalComments = data.total
  } catch (error: any) {
    const message = error.response?.data?.message || '加载评论失败'
    uiStore.showToast(message, 'error')
  }
}

async function loadReplies(rootId: number) {
  if (loadedRootIds.value.has(rootId)) return
  try {
    // 1. 加载里层回复（直接挂在该表层评论下，is_nested=false）
    const firstLayer = await commentStore.fetchComments({
      target_type: props.targetType,
      target_id: props.targetId,
      parent_id: rootId,
      is_nested: false,
      sort_by: currentSort.value,
      skip: 0,
      limit: 100
    }, true)

    // 2. 加载嵌套回复（is_nested=true，parent_id 同样等于 rootId）
    // 嵌套回复的 nested_parent_id 指向某条里层回复
    if (firstLayer.items.length > 0) {
      await commentStore.fetchComments({
        target_type: props.targetType,
        target_id: props.targetId,
        parent_id: rootId,
        is_nested: true,
        sort_by: currentSort.value,
        skip: 0,
        limit: 100
      }, true)
    }

    loadedRootIds.value.add(rootId)
  } catch (error: any) {
    const message = error.response?.data?.message || '加载回复失败'
    uiStore.showToast(message, 'error')
  }
}

function collapseReplies(rootId: number) {
  loadedRootIds.value.delete(rootId)
  // 移除该表层评论下的所有子评论（里层回复 + 嵌套回复）
  commentStore.comments = commentStore.comments.filter(
    (c) => c.parent_id !== rootId
  )
}

async function submitComment() {
  if (!newComment.value.trim()) return
  try {
    await commentStore.createComment({
      target_type: props.targetType,
      target_id: props.targetId,
      content: newComment.value.trim()
    })
    newComment.value = ''
  } catch (error: any) {
    const message = error.response?.data?.message || '评论发送失败'
    uiStore.showToast(message, 'error')
  }
}

watch(currentSort, () => {
  resetAndLoad()
  if (isExpanded.value) {
    loadRootComments()
  }
})

watch(currentPage, () => {
  loadedRootIds.value.clear()
  commentStore.comments = commentStore.comments.filter((c) => c.parent_id === null)
  if (isExpanded.value) {
    loadRootComments()
  }
})

watch(() => props.targetId, (newId, oldId) => {
  if (newId !== oldId) {
    isExpanded.value = false
    resetAndLoad()
  }
})

onMounted(() => {
  resetAndLoad()
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
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.sort-tabs {
  display: flex;
  gap: 8px;
}
.collapse-btn {
  padding: 4px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: all 0.2s;
}
.collapse-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--text-primary);
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
