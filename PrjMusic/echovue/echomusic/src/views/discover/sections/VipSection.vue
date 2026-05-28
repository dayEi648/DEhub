<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { getMusicPage } from '@/api/discover'
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
    musicData.value = await getMusicPage({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      vip: true,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    })
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
      <h2 class="section-title">
        <el-icon class="title-icon" :size="22"><Star /></el-icon>
        VIP 专属音乐
      </h2>
      <div class="section-tools">
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
      :show-vip-tag="true"
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
.title-icon {
  color: #f59e0b;
  margin-right: 8px;
  vertical-align: middle;
}
.section-tools {
  display: flex;
  align-items: center;
  gap: 10px;
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
