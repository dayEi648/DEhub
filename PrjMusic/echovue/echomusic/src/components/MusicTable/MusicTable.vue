<script setup lang="ts">
import { CaretRight, Star, StarFilled, Headset } from '@element-plus/icons-vue'
import { getUser } from '@/utils/authStorage'
import type { MusicVO } from '@/types/music'

const props = withDefaults(defineProps<{
  data: MusicVO[]
  loading: boolean
  total: number
  pageNum: number
  pageSize: number
  showRank?: boolean
  rankStart?: number
  showVipTag?: boolean
}>(), {
  showRank: false,
  rankStart: 1,
  showVipTag: false
})

const emit = defineEmits<{
  (e: 'play', row: MusicVO): void
  (e: 'add', id: number): void
  (e: 'pageChange', page: number): void
  (e: 'rowClick', row: MusicVO): void
}>()

function isCollected(musicId: number): boolean {
  return getUser()?.collectMusicIds?.includes(musicId) ?? false
}

function joinNames(names?: string[]) {
  return names?.filter(Boolean).join(' / ') || '未知作者'
}

function formatCount(n?: number) {
  if (n == null) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function onRowClick(row: MusicVO) {
  emit('rowClick', row)
}
</script>

<template>
  <div class="music-table-wrap">
    <el-table
      :data="data"
      v-loading="loading"
      class="music-table"
      @row-click="onRowClick"
    >
      <!-- 排名列 -->
      <el-table-column v-if="showRank" width="60">
        <template #default="{ $index }">
          <span class="rank-num" :class="{ top: $index + rankStart <= 3 }">
            {{ $index + rankStart }}
          </span>
        </template>
      </el-table-column>

      <!-- 歌曲列 -->
      <el-table-column label="歌曲" min-width="280">
        <template #default="{ row }: { row: MusicVO }">
          <div class="table-song">
            <div class="table-cover">
              <img v-if="row.image1Url" :src="row.image1Url" />
              <div v-else class="cover-placeholder small">
                <el-icon><Headset /></el-icon>
              </div>
            </div>
            <div class="table-song-info">
              <div class="table-song-name">
                {{ row.musicName }}
                <el-tag v-if="showVipTag || row.vip" size="small" type="warning" class="vip-tag">VIP</el-tag>
              </div>
              <div class="table-song-artist">{{ joinNames(row.authorNameList) }}</div>
            </div>
          </div>
        </template>
      </el-table-column>

      <!-- 专辑列 -->
      <el-table-column label="专辑" prop="albumName" min-width="160" />

      <!-- 热度列 -->
      <el-table-column label="热度" width="100">
        <template #default="{ row }">{{ row.hot }}</template>
      </el-table-column>

      <!-- 播放量列（可选显示） -->
      <el-table-column label="播放" width="100">
        <template #default="{ row }">{{ formatCount(row.playCount) }}</template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }: { row: MusicVO }">
          <el-button circle size="small" @click.stop="emit('play', row)">
            <el-icon><CaretRight /></el-icon>
          </el-button>
          <el-button circle size="small" @click.stop="emit('add', row.id)">
            <el-icon>
              <StarFilled v-if="isCollected(row.id)" />
              <Star v-else />
            </el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination
        :current-page="pageNum"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="emit('pageChange', $event)"
      />
    </div>
    <el-empty v-else-if="!loading" description="暂无数据" />
  </div>
</template>

<style scoped>
.music-table-wrap {
  width: 100%;
}

/* ===== Element Plus 表格暗黑主题彻底覆盖 ===== */
.music-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-row-hover-bg-color: rgba(139, 92, 246, 0.12);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-text-color: rgba(255, 255, 255, 0.7);
}

.music-table :deep(.el-table) {
  background: transparent;
}

.music-table :deep(.el-table__inner-wrapper) {
  background: transparent;
}

.music-table :deep(.el-table__body-wrapper) {
  background: transparent;
}

.music-table :deep(.el-table__header-wrapper) {
  background: transparent;
}

.music-table :deep(th.el-table__cell) {
  background: rgba(255, 255, 255, 0.04) !important;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.music-table :deep(td.el-table__cell) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.25s ease;
}

.music-table :deep(.el-table__row) {
  cursor: pointer;
  position: relative;
}

/* Hover 行增强效果：左侧渐变指示条 */
.music-table :deep(.el-table__row:hover td.el-table__cell:first-child)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: linear-gradient(180deg, #8b5cf6, #ec4899);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.5);
}

.music-table :deep(.el-loading-mask) {
  background: rgba(10, 6, 20, 0.6);
  backdrop-filter: blur(4px);
}

/* 排名数字样式 */
.rank-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
}

.rank-num.top {
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
  color: white;
  animation: rankPulse 2.5s ease-in-out infinite;
}

@keyframes rankPulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.3); }
  50% { transform: scale(1.08); box-shadow: 0 0 10px 2px rgba(245, 158, 11, 0.15); }
}

/* 歌曲信息布局 */
.table-song {
  display: flex;
  align-items: center;
  gap: 12px;
}

.table-cover {
  width: 44px;
  height: 44px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
}

.table-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.3);
}

.table-song-info {
  min-width: 0;
}

.table-song-name {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.vip-tag {
  margin-left: 6px;
  font-size: 10px;
  height: 18px;
  line-height: 16px;
}

.table-song-artist {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: #a78bfa;
  --el-pagination-text-color: rgba(255, 255, 255, 0.6);
  --el-pagination-button-disabled-color: rgba(255, 255, 255, 0.3);
}

.pagination-wrap :deep(.el-pagination button) {
  background: transparent;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 32px;
  height: 32px;
}

.pagination-wrap :deep(.el-pagination button:not(:disabled):hover) {
  color: #a78bfa;
  border-color: rgba(167, 139, 250, 0.3);
  background: rgba(107, 70, 193, 0.1);
}

.pagination-wrap :deep(.el-pager li) {
  background: transparent;
  border-radius: 8px;
  border: 1px solid transparent;
  min-width: 32px;
  height: 32px;
  line-height: 30px;
  font-size: 13px;
  margin: 0 4px;
  padding: 0;
}

.pagination-wrap :deep(.el-pager li:not(.is-active):hover) {
  color: #a78bfa;
  background: rgba(107, 70, 193, 0.12);
  border-color: rgba(167, 139, 250, 0.15);
}

.pagination-wrap :deep(.el-pager li.is-active) {
  background: #6b46c1;
  color: white;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(107, 70, 193, 0.4);
}
</style>
