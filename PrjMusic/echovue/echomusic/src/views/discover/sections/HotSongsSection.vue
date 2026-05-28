<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getMusicPage } from '@/api/discover'
import { useMusicTable } from '@/composables/useMusicTable'
import type { MusicVO, PageDataVo } from '@/types/music'
import MusicTable from '@/components/MusicTable/MusicTable.vue'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'

const musicData = ref<PageDataVo<MusicVO>>({ total: 0, records: [] })
const loading = ref(false)

const {
  pageNum, pageSize,
  addDialogVisible, addDialogMusicId,
  handlePageChange, onPlay, openAddDialog
} = useMusicTable()

async function loadData() {
  loading.value = true
  try {
    musicData.value = await getMusicPage({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      sortBy: 'hot',
      sortOrder: 'desc'
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
      <h2 class="section-title">热歌榜</h2>
      <span class="section-meta">共 {{ musicData.total }} 首</span>
    </div>

    <MusicTable
      :data="musicData.records"
      :loading="loading"
      :total="musicData.total"
      :page-num="pageNum"
      :page-size="pageSize"
      :show-rank="true"
      :rank-start="1 + (pageNum - 1) * pageSize"
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
.section-meta {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
