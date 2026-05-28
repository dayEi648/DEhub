<script setup lang="ts">
import { ref, onMounted } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface StatItem {
  icon: string
  label: string
  value: number
  suffix: string
  prefix: string
  decimals: number
  gradient: string
}

const stats: StatItem[] = [
  {
    icon: '🎧', label: '本周听歌', value: 23.5, suffix: ' 小时', prefix: '',
    decimals: 1, gradient: 'linear-gradient(135deg, #6b46c1, #ec4899)'
  },
  {
    icon: '💜', label: '最喜爱歌手', value: 0, suffix: '', prefix: '周杰伦',
    decimals: 0, gradient: 'linear-gradient(135deg, #ec4899, #f43f5e)'
  },
  {
    icon: '📝', label: '收藏歌单', value: 12, suffix: ' 个', prefix: '',
    decimals: 0, gradient: 'linear-gradient(135deg, #3b82f6, #8b5cf6)'
  },
  {
    icon: '🔥', label: '连续打卡', value: 7, suffix: ' 天', prefix: '',
    decimals: 0, gradient: 'linear-gradient(135deg, #f59e0b, #ef4444)'
  }
]

const sectionRef = ref<HTMLElement | null>(null)
const cardRefs = ref<(HTMLElement | null)[]>([])
const countUpValues = ref<string[]>(stats.map(s => s.prefix || (s.decimals > 0 ? '0.0' : '0')))

onMounted(() => {
  if (sectionRef.value) {
    gsap.from(sectionRef.value.querySelector('.section-header'), {
      y: 30, opacity: 0, duration: 0.8, ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value, start: 'top 85%' }
    })

    const cards = cardRefs.value.filter(Boolean) as HTMLElement[]
    gsap.from(cards, {
      y: 40, opacity: 0, duration: 0.7, stagger: 0.1,
      ease: 'power3.out',
      scrollTrigger: { trigger: sectionRef.value.querySelector('.stats-grid'), start: 'top 85%' }
    })
  }

  // Count-up animation
  stats.forEach((stat, idx) => {
    if (stat.value > 0) {
      const obj = { val: 0 }
      gsap.to(obj, {
        val: stat.value,
        duration: 2,
        ease: 'power2.out',
        delay: idx * 0.15,
        scrollTrigger: {
          trigger: sectionRef.value,
          start: 'top 80%',
          once: true
        },
        onUpdate: () => {
          const val = stat.decimals > 0
            ? obj.val.toFixed(stat.decimals)
            : Math.round(obj.val).toString()
          countUpValues.value[idx] = val + stat.suffix
        }
      })
    } else if (stat.prefix) {
      countUpValues.value[idx] = stat.prefix + stat.suffix
    }
  })
})
</script>

<template>
  <section ref="sectionRef" class="stats-section">
    <div class="section-header">
      <h3 class="section-title">
        <span class="title-icon">📊</span>
        你的音乐足迹
      </h3>
    </div>

    <div class="stats-grid">
      <div
        v-for="(stat, idx) in stats"
        :key="stat.label"
        :ref="(el) => { if (el) cardRefs[idx] = el as HTMLElement }"
        class="stat-card"
      >
        <div class="stat-icon-wrap" :style="{ background: stat.gradient }">
          <span class="stat-icon">{{ stat.icon }}</span>
        </div>
        <div class="stat-info">
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-value">{{ countUpValues[idx] }}</div>
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

.stats-section {
  padding: 24px 0 48px;
  position: relative;
  z-index: 2;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  transition: all 0.35s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(107, 70, 193, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.stat-icon {
  font-size: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
