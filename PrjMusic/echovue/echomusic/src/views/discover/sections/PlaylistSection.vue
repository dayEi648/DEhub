<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Collection } from '@element-plus/icons-vue'
import { getPlaylistPage, getHomeRecommendPlaylists } from '@/api/discover'
import type { PlaylistVO, PageDataVo } from '@/types/playlist'

const router = useRouter()

const recommendLoading = ref(false)
const recommendList = ref<PlaylistVO[]>([])

const loading = ref(false)
const playlistData = ref<PageDataVo<PlaylistVO>>({ total: 0, records: [] })
const pageNum = ref(1)
const pageSize = ref(20)
const sortBy = ref('hot')
const sortOrder = ref<'asc' | 'desc'>('desc')

const sortOptions = [
  { label: '热度', value: 'hot' },
  { label: '收藏数', value: 'collect_count' },
  { label: '播放数', value: 'play_count' },
  { label: '评论数', value: 'comment_count' }
]

async function loadRecommend() {
  recommendLoading.value = true
  try {
    recommendList.value = await getHomeRecommendPlaylists()
  } catch {
    recommendList.value = []
  } finally {
    recommendLoading.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    playlistData.value = await getPlaylistPage({
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      sortBy: sortBy.value,
      sortOrder: sortOrder.value
    })
  } catch {
    playlistData.value = { total: 0, records: [] }
  } finally {
    loading.value = false
  }
}

function handlePageChange(newPage: number) {
  pageNum.value = newPage
  loadData()
}

function handleSortChange() {
  pageNum.value = 1
  loadData()
}

function goPlaylistDetail(id: number) {
  router.push(`/playlist/${id}`)
}

function formatCount(n?: number) {
  if (n == null) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

onMounted(() => {
  loadRecommend()
  loadData()
})
</script>

<template>
  <section class="discover-section">
    <div class="recommend-block">
      <h3 class="block-title">个性推荐</h3>
      <div v-if="recommendLoading" class="recommend-loading">
        <el-skeleton :rows="1" animated />
      </div>
      <div v-else class="recommend-grid">
        <div
          v-for="pl in recommendList"
          :key="pl.id"
          class="media-card"
          @click="goPlaylistDetail(pl.id)"
        >
          <div class="media-cover">
            <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
            <div v-else class="cover-placeholder"><el-icon><Collection /></el-icon></div>
          </div>
          <div class="media-name" :title="pl.playlistName">{{ pl.playlistName }}</div>
          <div class="media-meta">{{ pl.songIds?.length || 0 }}首 · 收藏{{ formatCount(pl.collectCount) }}</div>
        </div>
      </div>
    </div>

    <div class="all-block">
      <div class="section-header-row">
        <h3 class="block-title">全部歌单</h3>
        <div class="section-tools">
          <el-select v-model="sortBy" size="small" class="sort-select" @change="handleSortChange">
            <el-option v-for="opt in sortOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <el-button size="small" :type="sortOrder === 'desc' ? 'primary' : 'default'" @click="sortOrder = 'desc'; handleSortChange()">降序</el-button>
          <el-button size="small" :type="sortOrder === 'asc' ? 'primary' : 'default'" @click="sortOrder = 'asc'; handleSortChange()">升序</el-button>
        </div>
      </div>

      <div v-loading="loading" class="card-grid">
        <div v-for="pl in playlistData.records" :key="pl.id" class="media-card" @click="goPlaylistDetail(pl.id)">
          <div class="media-cover large">
            <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
            <div v-else class="cover-placeholder"><el-icon><Collection /></el-icon></div>
          </div>
          <div class="media-name" :title="pl.playlistName">{{ pl.playlistName }}</div>
          <div class="media-meta">{{ pl.songIds?.length || 0 }}首 · 收藏{{ formatCount(pl.collectCount) }}</div>
        </div>
      </div>

      <div v-if="playlistData.total > 0" class="pagination-wrap">
        <el-pagination v-model:current-page="pageNum" :page-size="pageSize" :total="playlistData.total" layout="prev, pager, next" @current-change="handlePageChange" />
      </div>
      <el-empty v-else-if="!loading" description="暂无歌单" />
    </div>
  </section>
</template>

<style scoped>
.discover-section { padding: 8px 0; }
.recommend-block { margin-bottom: 40px; }
.block-title { font-size: 18px; font-weight: 700; color: #ffffff; margin-bottom: 16px; }
.recommend-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.all-block { padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.06); }
.card-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; }
.media-card { cursor: pointer; transition: transform 0.3s ease; }
.media-card:hover { transform: translateY(-4px); }
.media-cover { aspect-ratio: 1; border-radius: 12px; overflow: hidden; background: rgba(255,255,255,0.06); margin-bottom: 10px; }
.media-cover img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.4s ease; }
.media-card:hover .media-cover img { transform: scale(1.06); }
.cover-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.3); font-size: 32px; }
.media-name { font-size: 14px; font-weight: 500; color: #e2e8f0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 4px; }
.media-meta { font-size: 12px; color: rgba(255,255,255,0.4); }
.section-tools { display: flex; align-items: center; gap: 10px; }
.sort-select { width: 110px; }
.sort-select :deep(.el-input__wrapper) { background: rgba(255,255,255,0.06); }
.sort-select :deep(.el-input__inner) { color: #e2e8f0; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 24px; }
@media (max-width: 1024px) {
  .recommend-grid, .card-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 640px) {
  .recommend-grid, .card-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
