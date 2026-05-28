<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getMusicPage, getTopTags } from '@/api/discover'
import { useMusicTable } from '@/composables/useMusicTable'
import type { MusicVO, PageDataVo } from '@/types/music'
import MusicTable from '@/components/MusicTable/MusicTable.vue'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'

const route = useRoute()

const tags = ref<string[]>([])
const activeTag = ref('')
const tagsLoading = ref(false)

const musicData = ref<PageDataVo<MusicVO>>({ total: 0, records: [] })
const loading = ref(false)

const {
  pageNum, pageSize, sortBy, sortOrder, sortOptions,
  addDialogVisible, addDialogMusicId,
  handlePageChange, handleSortChange, onPlay, openAddDialog
} = useMusicTable()

async function loadTags() {
  tagsLoading.value = true
  try {
    tags.value = await getTopTags('interest', 20)
    const queryTag = route.query.tag as string
    if (queryTag && tags.value.includes(queryTag)) {
      activeTag.value = queryTag
    } else if (tags.value.length > 0) {
      activeTag.value = tags.value[0] || ''
    }
    await loadResults()
  } catch {
    tags.value = []
  } finally {
    tagsLoading.value = false
  }
}

async function loadResults() {
  const tag = activeTag.value
  if (!tag) return
  loading.value = true
  try {
    musicData.value = await getMusicPage({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      interestTags: [tag],
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    })
  } catch {
    musicData.value = { total: 0, records: [] }
  } finally {
    loading.value = false
  }
}

function selectTag(tag: string) {
  activeTag.value = tag
  pageNum.value = 1
  loadResults()
}

watch(() => route.query.tag, (newTag) => {
  if (newTag && tags.value.includes(newTag as string)) {
    activeTag.value = newTag as string
    pageNum.value = 1
    loadResults()
  }
})

onMounted(loadTags)
</script>

<template>
  <section class="discover-section">
    <!-- 标签筛选 -->
    <div v-loading="tagsLoading" class="tag-filter">
      <div
        v-for="tag in tags"
        :key="tag"
        class="tag-item"
        :class="{ active: activeTag === tag }"
        @click="selectTag(tag)"
      >
        {{ tag }}
      </div>
      <el-empty v-if="!tagsLoading && tags.length === 0" description="暂无标签数据" />
    </div>

    <!-- 排序 -->
    <div class="sort-bar">
      <span class="sort-label">排序：</span>
      <el-select v-model="sortBy" size="small" class="sort-select" @change="handleSortChange(loadResults)">
        <el-option v-for="opt in sortOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
      </el-select>
      <el-button size="small" :type="sortOrder === 'desc' ? 'primary' : 'default'" @click="sortOrder = 'desc'; handleSortChange(loadResults)">降序</el-button>
      <el-button size="small" :type="sortOrder === 'asc' ? 'primary' : 'default'" @click="sortOrder = 'asc'; handleSortChange(loadResults)">升序</el-button>
    </div>

    <MusicTable
      :data="musicData.records"
      :loading="loading"
      :total="musicData.total"
      :page-num="pageNum"
      :page-size="pageSize"
      @play="onPlay"
      @add="openAddDialog"
      @page-change="handlePageChange($event, loadResults)"
      @row-click="onPlay"
    />

    <AddToPlaylistDialog
      :visible="addDialogVisible"
      :music-id="addDialogMusicId"
      @submit="addDialogVisible = false; loadResults()"
      @cancel="addDialogVisible = false"
    />
  </section>
</template>

<style scoped>
.discover-section {
  padding: 8px 0;
}
.tag-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
  min-height: 40px;
}
.tag-item {
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  cursor: pointer;
  transition: all 0.25s ease;
}
.tag-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}
.tag-item.active {
  background: linear-gradient(135deg, #6b46c1 0%, #8b5cf6 100%);
  color: white;
  border-color: transparent;
}
.sort-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.sort-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}
.sort-select {
  width: 110px;
}
.sort-select :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
}
.sort-select :deep(.el-input__inner) {
  color: #e2e8f0;
}
</style>
