<template>
  <div class="pagination">
    <button
      class="page-btn"
      :disabled="currentPage <= 1"
      @click="$emit('update:currentPage', currentPage - 1)"
    >
      ←
    </button>
    <button
      v-for="p in visiblePages"
      :key="p"
      class="page-btn"
      :class="{ active: p === currentPage }"
      @click="$emit('update:currentPage', p)"
    >
      {{ p }}
    </button>
    <button
      class="page-btn"
      :disabled="currentPage >= totalPages"
      @click="$emit('update:currentPage', currentPage + 1)"
    >
      →
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  total: number
  pageSize?: number
  currentPage: number
}
const props = withDefaults(defineProps<Props>(), {
  pageSize: 20
})

defineEmits<{
  'update:currentPage': [page: number]
}>()

const totalPages = computed(() => Math.ceil(props.total / props.pageSize))

const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, props.currentPage - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1)
  }
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px 0;
}
.page-btn {
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
}
.page-btn:hover:not(:disabled):not(.active) {
  background: rgba(0, 0, 0, 0.04);
}
.page-btn.active {
  background: var(--text-primary);
  color: var(--text-white);
}
.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
