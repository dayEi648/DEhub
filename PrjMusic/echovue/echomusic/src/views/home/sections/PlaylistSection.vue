<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CaretRight, Headset } from '@element-plus/icons-vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useTilt } from '@/composables/useTilt'
import type { PlaylistItem } from '../useHomePage'

const router = useRouter()

gsap.registerPlugin(ScrollTrigger)

const props = defineProps<{
  playlists: PlaylistItem[]
}>()

const emit = defineEmits<{
  (e: 'click', pl: PlaylistItem): void
}>()

// 情绪色彩映射
const emotionColors: Record<string, { from: string; to: string }> = {
  '流行': { from: '#6b46c1', to: '#ec4899' },
  '热歌': { from: '#6b46c1', to: '#ec4899' },
  '摇滚': { from: '#f59e0b', to: '#ef4444' },
  '激情': { from: '#f59e0b', to: '#ef4444' },
  '电子': { from: '#3b82f6', to: '#8b5cf6' },
  '未来': { from: '#3b82f6', to: '#8b5cf6' },
  '轻音乐': { from: '#06b6d4', to: '#10b981' },
  '治愈': { from: '#06b6d4', to: '#10b981' },
  '怀旧': { from: '#d97706', to: '#fbbf24' },
  '经典': { from: '#d97706', to: '#fbbf24' },
  '平静': { from: '#64748b', to: '#94a3b8' },
  '睡眠': { from: '#64748b', to: '#94a3b8' },
}

function getEmotionColor(tag: string) {
  return emotionColors[tag] || { from: '#6b46c1', to: '#ec4899' }
}

const sectionRef = ref<HTMLElement | null>(null)
const cardRefs = ref<(HTMLElement | null)[]>([])

// 3D tilt for each card
const tiltRefs = ref<(HTMLElement | null)[]>([])

onMounted(() => {
  if (sectionRef.value) {
    gsap.from(sectionRef.value.querySelector('.section-header'), {
      y: 30,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: sectionRef.value,
        start: 'top 85%',
        toggleActions: 'play none none none'
      }
    })

    const cards = cardRefs.value.filter(Boolean) as HTMLElement[]
    if (cards.length === 0) return
    gsap.from(cards, {
      y: 50,
      opacity: 0,
      duration: 0.7,
      stagger: 0.08,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: sectionRef.value.querySelector('.playlist-grid-v2'),
        start: 'top 85%',
        toggleActions: 'play none none none'
      }
    })
  }
})
</script>

<template>
  <section ref="sectionRef" class="playlist-section-v2">
    <div class="section-header">
      <h3 class="section-title">
        <span class="title-icon">✨</span>
        推荐歌单
      </h3>
      <a class="section-more" href="javascript:;" @click="router.push({ path: '/discover', query: { tab: 'playlist' } })">
        查看全部
        <el-icon><CaretRight /></el-icon>
      </a>
    </div>

    <div class="playlist-grid-v2">
      <div
        v-for="(pl, idx) in playlists"
        :key="pl.id"
        :ref="(el) => { if (el) cardRefs[idx] = el as HTMLElement }"
        class="playlist-card-v2"
        :style="{ '--card-accent': getEmotionColor(pl.tag).from }"
        @click="emit('click', pl)"
      >
        <div class="card-glow" :style="{ background: `radial-gradient(circle at 50% 0%, ${getEmotionColor(pl.tag).from}30, transparent 70%)` }" />
        <div class="playlist-cover-v2">
          <img
            v-if="pl.coverUrl"
            :src="pl.coverUrl"
            :alt="pl.name"
            class="playlist-cover-img-v2"
          />
          <div v-else class="img-placeholder-v2">
            <el-icon size="32"><Headset /></el-icon>
          </div>
          <span
            class="playlist-tag-v2"
            :style="{ background: `linear-gradient(135deg, ${getEmotionColor(pl.tag).from}, ${getEmotionColor(pl.tag).to})` }"
          >
            {{ pl.tag }}
          </span>
          <div class="playlist-play-v2">
            <el-icon><CaretRight /></el-icon>
          </div>
        </div>
        <div class="playlist-info-v2">
          <div class="playlist-name-v2">{{ pl.name }}</div>
          <div class="playlist-meta-v2">
            <el-icon size="12"><Headset /></el-icon>
            {{ pl.playCount }}次播放
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

.playlist-section-v2 {
  padding: 24px 0;
  position: relative;
  z-index: 2;
}

.playlist-grid-v2 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
}

.playlist-card-v2 {
  position: relative;
  border-radius: 20px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform-style: preserve-3d;
}

/* Gradient border effect */
.playlist-card-v2::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 20px;
  padding: 1px;
  background: linear-gradient(135deg, var(--card-accent, #6b46c1), transparent 60%);
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.playlist-card-v2:hover::before {
  opacity: 0.8;
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 120px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.playlist-card-v2:hover .card-glow {
  opacity: 1;
}

.playlist-card-v2:hover {
  transform: translateY(-8px);
  border-color: rgba(255, 255, 255, 0.1);
  box-shadow:
    0 20px 50px rgba(0, 0, 0, 0.4),
    0 0 40px rgba(107, 70, 193, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.playlist-cover-v2 {
  aspect-ratio: 1;
  position: relative;
  overflow: hidden;
}

.playlist-cover-img-v2 {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.playlist-card-v2:hover .playlist-cover-img-v2 {
  transform: scale(1.1);
}

.img-placeholder-v2 {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.1) 0%, rgba(236, 72, 153, 0.05) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
}

.playlist-tag-v2 {
  position: absolute;
  top: 10px;
  left: 10px;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  color: white;
  font-weight: 600;
  z-index: 1;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.playlist-play-v2 {
  position: absolute;
  bottom: 12px;
  right: 12px;
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateY(10px) scale(0.8);
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
  box-shadow: 0 4px 20px rgba(107, 70, 193, 0.5);
}

.playlist-card-v2:hover .playlist-play-v2 {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.playlist-play-v2 .el-icon {
  color: white;
  font-size: 20px;
  margin-left: 2px;
}

.playlist-info-v2 {
  padding: 16px;
  position: relative;
  z-index: 1;
}

.playlist-name-v2 {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playlist-meta-v2 {
  font-size: 12px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 4px;
}

@media (max-width: 1200px) {
  .playlist-grid-v2 {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .playlist-grid-v2 {
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
}

@media (max-width: 640px) {
  .playlist-grid-v2 {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .section-title {
    font-size: 18px;
  }
}
</style>
