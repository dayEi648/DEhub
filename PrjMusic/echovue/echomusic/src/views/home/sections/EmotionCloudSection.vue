<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

const router = useRouter()

function goToDiscover(tag: string) {
  router.push({ path: '/discover', query: { tab: 'emotion', tag } })
}

const emotions = [
  { label: '浪漫', en: 'Romance', color: '#6b46c1', glow: 'rgba(107, 70, 193, 0.3)', size: 'lg', delay: 0 },
  { label: '忧伤', en: 'Melancholy', color: '#3b82f6', glow: 'rgba(59, 130, 246, 0.3)', size: 'md', delay: 0.5 },
  { label: '活力', en: 'Energy', color: '#f59e0b', glow: 'rgba(245, 158, 11, 0.3)', size: 'lg', delay: 1 },
  { label: '治愈', en: 'Healing', color: '#10b981', glow: 'rgba(16, 185, 129, 0.3)', size: 'md', delay: 1.5 },
  { label: '激情', en: 'Passion', color: '#ec4899', glow: 'rgba(236, 72, 153, 0.3)', size: 'sm', delay: 0.3 },
  { label: '怀旧', en: 'Nostalgia', color: '#d97706', glow: 'rgba(217, 119, 6, 0.3)', size: 'md', delay: 0.8 },
  { label: '平静', en: 'Calm', color: '#64748b', glow: 'rgba(100, 116, 139, 0.3)', size: 'sm', delay: 1.2 },
  { label: '梦幻', en: 'Dreamy', color: '#8b5cf6', glow: 'rgba(139, 92, 246, 0.3)', size: 'sm', delay: 0.2 },
]

const sectionRef = ref<HTMLElement | null>(null)

onMounted(() => {
  if (sectionRef.value) {
    gsap.from(sectionRef.value.querySelector('.section-header'), {
      y: 30, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value, start: 'top 85%' }
    })

    const tags = sectionRef.value.querySelectorAll('.emotion-tag-v2')
    gsap.from(tags, {
      scale: 0.5, opacity: 0, duration: 0.6, stagger: 0.08,
      ease: 'back.out(1.7)',
      scrollTrigger: { trigger: sectionRef.value.querySelector('.emotion-cloud-v2'), start: 'top 85%' }
    })
  }
})
</script>

<template>
  <section ref="sectionRef" class="emotion-section-v2">
    <div class="section-header">
      <h3 class="section-title">
        <span class="title-icon">🎭</span>
        探索你的情绪
      </h3>
    </div>

    <div class="emotion-cloud-v2">
      <div
        v-for="emotion in emotions"
        :key="emotion.label"
        class="emotion-tag-v2"
        :class="`size-${emotion.size}`"
        :style="{
          '--tag-color': emotion.color,
          '--tag-glow': emotion.glow,
          animationDelay: `${emotion.delay}s`
        }"
        @click="goToDiscover(emotion.label)"
      >
        <span class="tag-dot" :style="{ background: emotion.color }" />
        <span class="tag-label">{{ emotion.label }}</span>
        <span class="tag-en">{{ emotion.en }}</span>
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

.emotion-section-v2 {
  padding: 24px 0 40px;
  position: relative;
  z-index: 2;
}

.emotion-cloud-v2 {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 16px 8px;
  justify-content: center;
}

.emotion-tag-v2 {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.emotion-tag-v2:hover {
  transform: translateY(-4px) scale(1.12);
  border-color: var(--tag-color);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 8px 30px var(--tag-glow);
  color: #e2e8f0;
}

.tag-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
  transition: transform 0.3s ease;
}

.emotion-tag-v2:hover .tag-dot {
  transform: scale(1.3);
}

.tag-label {
  font-weight: 600;
}

.tag-en {
  font-size: 11px;
  opacity: 0.5;
  font-weight: 400;
}

.size-lg {
  font-size: 16px;
  padding: 14px 28px;
}

.size-sm {
  font-size: 13px;
  padding: 10px 18px;
}

@media (max-width: 640px) {
  .emotion-cloud-v2 {
    gap: 10px;
  }
  .emotion-tag-v2 {
    padding: 10px 16px;
    font-size: 13px;
  }
  .tag-en {
    display: none;
  }
}
</style>
