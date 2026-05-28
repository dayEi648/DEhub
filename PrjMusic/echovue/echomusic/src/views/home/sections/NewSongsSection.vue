<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CaretRight, Clock } from '@element-plus/icons-vue'
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

function getDaysAgo(idx: number) {
  const days = [1, 2, 3, 5, 7, 14]
  return days[idx % days.length]
}

onMounted(() => {
  if (sectionRef.value) {
    gsap.from(sectionRef.value.querySelector('.section-header'), {
      y: 30, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value, start: 'top 85%' }
    })

    const cards = sectionRef.value.querySelectorAll('.new-song-card')
    if (cards.length === 0) return
    gsap.from(cards, {
      y: 60, opacity: 0, scale: 0.95, duration: 0.8, stagger: 0.12,
      ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value.querySelector('.new-songs-grid'), start: 'top 85%' }
    })
  }
})
</script>

<template>
  <section ref="sectionRef" class="new-songs-section">
    <div class="section-header">
      <h3 class="section-title">
        <span class="title-icon">🆕</span>
        新歌速递
      </h3>
      <a class="section-more" href="javascript:;" @click="router.push({ path: '/discover', query: { tab: 'new' } })">
        查看全部
        <el-icon><CaretRight /></el-icon>
      </a>
    </div>

    <div class="new-songs-grid">
      <div
        v-for="(song, idx) in songs.slice(0, 4)"
        :key="song.id"
        class="new-song-card"
        @click="emit('play', song)"
      >
        <div class="new-song-cover-wrap">
          <img v-if="song.coverUrl" :src="song.coverUrl" :alt="song.name" class="new-song-cover" />
          <div v-else class="new-song-cover-placeholder">
            <el-icon size="36"><CaretRight /></el-icon>
          </div>
          <span class="new-badge">NEW</span>
          <div class="new-song-play-overlay">
            <div class="new-song-play-btn">
              <el-icon><CaretRight /></el-icon>
            </div>
          </div>
        </div>
        <div class="new-song-info">
          <div class="new-song-name">{{ song.name }}</div>
          <div class="new-song-artist">{{ song.artist }}</div>
          <div class="new-song-meta">
            <span class="days-ago">{{ getDaysAgo(idx) }}天前</span>
            <span v-if="song.duration" class="new-song-duration">
              <el-icon size="11"><Clock /></el-icon>
              {{ song.duration }}
            </span>
          </div>
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

.new-songs-section {
  padding: 24px 0;
  position: relative;
  z-index: 2;
}

.new-songs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.new-song-card {
  display: flex;
  gap: 20px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.new-song-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(107, 70, 193, 0.2);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(107, 70, 193, 0.08);
}

.new-song-cover-wrap {
  width: 120px;
  height: 120px;
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;
}

.new-song-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.new-song-card:hover .new-song-cover {
  transform: scale(1.08);
}

.new-song-cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.1), rgba(236, 72, 153, 0.05));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.new-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #10b981, #34d399);
  border-radius: 20px;
  font-size: 10px;
  color: white;
  font-weight: 700;
  z-index: 1;
}

.new-song-play-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.new-song-card:hover .new-song-play-overlay {
  opacity: 1;
}

.new-song-play-btn {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6b46c1, #ec4899);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(107, 70, 193, 0.4);
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 4px 20px rgba(107, 70, 193, 0.4); }
  50% { box-shadow: 0 4px 30px rgba(107, 70, 193, 0.6), 0 0 20px rgba(236, 72, 153, 0.3); }
}

.new-song-play-btn .el-icon {
  color: white;
  font-size: 22px;
  margin-left: 2px;
}

.new-song-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8px;
  min-width: 0;
}

.new-song-name {
  font-size: 16px;
  font-weight: 700;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.new-song-artist {
  font-size: 13px;
  color: #94a3b8;
}

.new-song-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.days-ago {
  font-size: 12px;
  color: #64748b;
  padding: 3px 10px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
}

.new-song-duration {
  font-size: 12px;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 900px) {
  .new-songs-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .new-song-card {
    flex-direction: column;
    gap: 12px;
  }
  .new-song-cover-wrap {
    width: 100%;
    height: auto;
    aspect-ratio: 1;
  }
}
</style>
