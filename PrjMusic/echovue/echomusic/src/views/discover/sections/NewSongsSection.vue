<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMusicPage, buildNewSongsQuery } from '@/api/discover'
import { useMusicTable } from '@/composables/useMusicTable'
import type { MusicVO, PageDataVo } from '@/types/music'
import MusicTable from '@/components/MusicTable/MusicTable.vue'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'

const musicData = ref<PageDataVo<MusicVO>>({ total: 0, records: [] })
const loading = ref(false)

const {
  pageNum, pageSize, sortBy, sortOrder, sortOptions,
  addDialogVisible, addDialogMusicId,
  handlePageChange, handleSortChange, onPlay, openAddDialog
} = useMusicTable()

async function loadData() {
  loading.value = true
  try {
    const params = buildNewSongsQuery(pageNum.value, pageSize.value, sortBy.value, sortOrder.value)
    musicData.value = await getMusicPage(params)
  } catch {
    musicData.value = { total: 0, records: [] }
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <section class="discover-section">
    <div class="section-header-row">
      <h2 class="section-title">新歌榜</h2>
      <div class="section-tools">
        <span class="section-note">近一个月发布的歌曲</span>
        <el-select v-model="sortBy" size="small" class="sort-select" @change="handleSortChange(loadData)">
          <el-option v-for="opt in sortOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>
        <el-button size="small" :type="sortOrder === 'desc' ? 'primary' : 'default'" @click="sortOrder = 'desc'; handleSortChange(loadData)">降序</el-button>
        <el-button size="small" :type="sortOrder === 'asc' ? 'primary' : 'default'" @click="sortOrder = 'asc'; handleSortChange(loadData)">升序</el-button>
      </div>
    </div>

    <MusicTable
      :data="musicData.records"
      :loading="loading"
      :total="musicData.total"
      :page-num="pageNum"
      :page-size="pageSize"
      @play="onPlay"
      @add="openAddDialog"
      @page-change="handlePageChange($event, loadData)"
      @row-click="onPlay"
    />

    <AddToPlaylistDialog
      :visible="addDialogVisible"
      :music-id="addDialogMusicId"
      @submit="addDialogVisible = false; loadData()"
      @cancel="addDialogVisible = false"
    />
  </section>
</template>

<style scoped>
.discover-section {
  padding: 8px 0;
}
.section-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}
.section-note {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-right: 8px;
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
