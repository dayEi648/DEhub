<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CaretRight, Clock, ArrowUp, ArrowDown, Minus } from '@element-plus/icons-vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import type { SongItem } from '../useHomePage'

const router = useRouter()

gsap.registerPlugin(ScrollTrigger)

const props = defineProps<{
  songs: SongItem[]
}>()

const emit = defineEmits<{
  (e: 'play', song: SongItem): void
}>()

const sectionRef = ref<HTMLElement | null>(null)
const coverFailed = ref<Record<number, boolean>>({})

function onCoverError(songId: number) {
  coverFailed.value[songId] = true
}

function getRankStyle(idx: number) {
  if (idx === 0) return { background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)', boxShadow: '0 2px 10px rgba(251, 191, 36, 0.4)' }
  if (idx === 1) return { background: 'linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%)', boxShadow: '0 2px 10px rgba(226, 232, 240, 0.3)' }
  if (idx === 2) return { background: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)', boxShadow: '0 2px 10px rgba(217, 119, 6, 0.3)' }
  return { background: 'rgba(255, 255, 255, 0.05)', color: '#64748b' }
}

function getHeatLevel(song: SongItem, _idx: number): { label: string; color: string; bg: string } {
  // 优先使用 hot 表的 hotLevel（0冷/1温/2热/3爆）
  if (song.hotLevel != null) {
    const level = song.hotLevel
    if (level >= 3) return { label: '火', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' }
    if (level >= 2) return { label: '热', color: '#f97316', bg: 'rgba(249, 115, 22, 0.15)' }
    if (level >= 1) return { label: '温', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)' }
    return { label: '冷', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)' }
  }

  // 兜底：使用 musics 表的 hot 字段做相对排序
  if (song.hot != null && props.songs.length > 0) {
    const maxHot = Math.max(...props.songs.map(s => s.hot || 0))
    const ratio = maxHot > 0 ? song.hot / maxHot : 0
    if (ratio >= 0.8) return { label: '火', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.15)' }
    if (ratio >= 0.5) return { label: '热', color: '#f97316', bg: 'rgba(249, 115, 22, 0.15)' }
    if (ratio >= 0.2) return { label: '温', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)' }
    return { label: '冷', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.15)' }
  }

  // 最终兜底：默认"温"
  return { label: '温', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)' }
}

function getTrend(song: SongItem) {
  // 优先使用 hot 表的 trend
  const trend = song.trend
  if (trend === 'up') return { icon: ArrowUp, color: '#22c55e', label: '上升' }
  if (trend === 'down') return { icon: ArrowDown, color: '#ef4444', label: '下降' }
  if (trend === 'stable') return { icon: Minus, color: '#94a3b8', label: '平稳' }

  // 空值兜底：显示 "-"
  return { icon: Minus, color: '#94a3b8', label: '-' }
}

onMounted(() => {
  if (sectionRef.value) {
    gsap.from(sectionRef.value.querySelector('.section-header'), {
      y: 30, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value, start: 'top 85%' }
    })

    const rows = sectionRef.value.querySelectorAll('.hot-song-row')
    if (rows.length === 0) return
    gsap.from(rows, {
      x: -40, opacity: 0, duration: 0.6, stagger: 0.06,
      ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value.querySelector('.hot-songs-list'), start: 'top 85%' }
    })
  }
})
</script>

<template>
  <section ref="sectionRef" class="hot-songs-section">
    <div class="section-header">
      <h3 class="section-title">
        <span class="title-icon">🔥</span>
        热门音乐
      </h3>
      <a class="section-more" href="javascript:;" @click="router.push({ path: '/discover', query: { tab: 'hot' } })">
        查看全部
        <el-icon><CaretRight /></el-icon>
      </a>
    </div>

    <div class="hot-songs-list">
      <div
        v-for="(song, idx) in songs.slice(0, 10)"
        :key="song.id"
        class="hot-song-row"
        @click="emit('play', song)"
      >
        <div class="rank-badge" :style="getRankStyle(idx)">
          <template v-if="idx < 3">
            <span class="rank-medal">{{ ['🥇', '🥈', '🥉'][idx] }}</span>
          </template>
          <template v-else>
            <span class="rank-number">{{ String(idx + 1).padStart(2, '0') }}</span>
          </template>
        </div>

        <div class="song-cover-small">
          <img v-if="song.coverUrl && !coverFailed[song.id]" :src="song.coverUrl" :alt="song.name" @error="onCoverError(song.id)" />
          <div v-else class="cover-placeholder">
            <el-icon size="20"><CaretRight /></el-icon>
          </div>
          <div class="song-play-btn-small">
            <el-icon><CaretRight /></el-icon>
          </div>
        </div>

        <div class="song-info-row">
          <div class="song-name-row">{{ song.name }}</div>
          <div class="song-artist-row">{{ song.artist }}</div>
        </div>

        <div class="song-meta-right">
          <div class="heat-badge" :style="{ color: getHeatLevel(song, idx).color, background: getHeatLevel(song, idx).bg }">
            {{ getHeatLevel(song, idx).label }}
          </div>
          <div class="trend-icon" :style="{ color: getTrend(song).color }" :title="getTrend(song).label">
            <el-icon><component :is="getTrend(song).icon" /></el-icon>
          </div>
        </div>

        <div class="song-duration-row" v-if="song.duration">
          <el-icon size="11"><Clock /></el-icon>
          {{ song.duration }}
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 20px;
}

.section-more {
  font-size: 13px;
  color: #64748b;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.section-more:hover {
  color: #a78bfa;
}

.hot-songs-section {
  padding: 24px 0;
  position: relative;
  z-index: 2;
}

.hot-songs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-song-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.hot-song-row:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(107, 70, 193, 0.15);
  transform: translateX(4px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.rank-badge {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  transition: transform 0.3s ease;
}

.hot-song-row:hover .rank-badge {
  transform: scale(1.1);
}

.rank-medal {
  font-size: 20px;
}

.rank-number {
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
}

.song-cover-small {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.song-cover-small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.1), rgba(236, 72, 153, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.song-play-btn-small {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.hot-song-row:hover .song-play-btn-small {
  opacity: 1;
}

.song-play-btn-small .el-icon {
  color: white;
  font-size: 20px;
}

.song-info-row {
  flex: 1;
  min-width: 0;
}

.song-name-row {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
}

.song-artist-row {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.song-meta-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.heat-badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.trend-icon {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.song-duration-row {
  font-size: 12px;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
  width: 50px;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .hot-song-row {
    gap: 12px;
    padding: 10px 12px;
  }
  .song-meta-right {
    display: none;
  }
  .song-duration-row {
    display: none;
  }
}
</style>
