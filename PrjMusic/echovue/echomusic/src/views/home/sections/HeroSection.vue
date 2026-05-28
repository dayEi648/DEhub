<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTypewriter } from '@/composables/useTypewriter'
import { Headset, Compass } from '@element-plus/icons-vue'

const router = useRouter()

function goToAiRecommend() {
  router.push({
    path: '/ai-chat',
    state: { autoMessage: '根据我的听歌习惯推荐音乐' }
  })
}

const props = defineProps<{
  displayName: string
}>()

const currentHour = new Date().getHours()
const greeting = computed(() => {
  if (currentHour < 6) return '夜深了'
  if (currentHour < 11) return '早上好'
  if (currentHour < 14) return '中午好'
  if (currentHour < 18) return '下午好'
  return '晚上好'
})

const dateStr = computed(() => {
  return new Date().toLocaleDateString('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

const quotes = [
  '音乐是记忆的回声，它在灵魂深处回荡',
  '每一段旋律，都是时光的低语',
  '让音符带走疲惫，让节奏唤醒心跳',
  '在声波中寻找失落的情绪碎片',
]
const randomQuote = quotes[Math.floor(Math.random() * quotes.length)] ?? ''

const { displayText: typedQuote, isDone } = useTypewriter(randomQuote, {
  speed: 70,
  delay: 600
})
</script>

<template>
  <section class="hero-section-v2">
    <div class="hero-glass">
      <div class="hero-left">
        <div class="hero-greeting">
          <span class="greeting-emoji">👋</span>
          <span class="greeting-text">{{ greeting }}，<strong>{{ displayName }}</strong></span>
        </div>
        <h1 class="hero-title">
          今天想听什么？
        </h1>
        <div class="hero-quote">
          <span class="quote-mark">"</span>
          <span class="quote-text">{{ typedQuote }}<span v-if="!isDone" class="quote-cursor">|</span></span>
          <span class="quote-mark">"</span>
        </div>
        <div class="hero-actions">
          <button class="hero-btn hero-btn-primary" @click="goToAiRecommend">
            <el-icon><Headset /></el-icon>
            <span>个性推荐</span>
          </button>
          <button class="hero-btn hero-btn-secondary" @click="router.push('/discover')">
            <el-icon><Compass /></el-icon>
            <span>探索发现</span>
          </button>
        </div>
      </div>

      <div class="hero-right">
        <!-- 动态声波可视化 -->
        <div class="sound-visualizer">
          <div v-for="i in 24" :key="i" class="viz-bar" :style="{ '--i': i }" />
        </div>
        <div class="mood-indicator">
          <span class="mood-dot mood-romance" />
          <span class="mood-label">浪漫</span>
          <span class="mood-sep">·</span>
          <span class="mood-dot mood-calm" />
          <span class="mood-label">平静</span>
          <span class="mood-sep">·</span>
          <span class="mood-dot mood-energy" />
          <span class="mood-label">活力</span>
        </div>
      </div>
    </div>
    <div class="hero-date">{{ dateStr }}</div>
  </section>
</template>

<style scoped>
.hero-section-v2 {
  position: relative;
  padding: 32px 0 24px;
  z-index: 2;
}

.hero-glass {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
  padding: 36px 40px;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.08) 0%, rgba(236, 72, 153, 0.04) 50%, rgba(6, 182, 212, 0.03) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 24px;
  position: relative;
  overflow: hidden;
}

.hero-glass::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(107, 70, 193, 0.12) 0%, transparent 70%);
  pointer-events: none;
}

.hero-glass::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(236, 72, 153, 0.08) 0%, transparent 70%);
  pointer-events: none;
}

.hero-left {
  flex: 1;
  position: relative;
  z-index: 1;
}

.hero-greeting {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: #94a3b8;
  margin-bottom: 12px;
}

.greeting-emoji {
  font-size: 20px;
}

.greeting-text strong {
  color: #e2e8f0;
  font-weight: 600;
}

.hero-title {
  font-size: 32px;
  font-weight: 800;
  color: #ffffff;
  margin-bottom: 16px;
  letter-spacing: -0.5px;
  background: linear-gradient(90deg, #e2e8f0 0%, #c4b5fd 50%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-quote {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: 24px;
  min-height: 28px;
}

.quote-mark {
  font-size: 24px;
  color: rgba(107, 70, 193, 0.5);
  line-height: 1;
  font-family: Georgia, serif;
}

.quote-text {
  font-size: 15px;
  color: #94a3b8;
  font-style: italic;
  line-height: 1.6;
}

.quote-cursor {
  color: #ec4899;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.hero-actions {
  display: flex;
  gap: 12px;
}

.hero-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.hero-btn-primary {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  color: white;
  box-shadow: 0 4px 20px rgba(107, 70, 193, 0.4);
}

.hero-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(107, 70, 193, 0.5);
}

.hero-btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.hero-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(107, 70, 193, 0.3);
}

/* Right side - Sound Visualizer */
.hero-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  position: relative;
  z-index: 1;
  min-width: 200px;
}

.sound-visualizer {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 80px;
}

.viz-bar {
  width: 4px;
  background: linear-gradient(to top, #6b46c1, #ec4899);
  border-radius: 2px;
  animation: vizWave 1.2s ease-in-out infinite;
  animation-delay: calc(var(--i) * 0.05s);
}

.viz-bar:nth-child(1) { height: 20%; }
.viz-bar:nth-child(2) { height: 45%; }
.viz-bar:nth-child(3) { height: 70%; }
.viz-bar:nth-child(4) { height: 35%; }
.viz-bar:nth-child(5) { height: 85%; }
.viz-bar:nth-child(6) { height: 55%; }
.viz-bar:nth-child(7) { height: 40%; }
.viz-bar:nth-child(8) { height: 75%; }
.viz-bar:nth-child(9) { height: 30%; }
.viz-bar:nth-child(10) { height: 65%; }
.viz-bar:nth-child(11) { height: 50%; }
.viz-bar:nth-child(12) { height: 80%; }
.viz-bar:nth-child(13) { height: 25%; }
.viz-bar:nth-child(14) { height: 60%; }
.viz-bar:nth-child(15) { height: 45%; }
.viz-bar:nth-child(16) { height: 70%; }
.viz-bar:nth-child(17) { height: 35%; }
.viz-bar:nth-child(18) { height: 55%; }
.viz-bar:nth-child(19) { height: 40%; }
.viz-bar:nth-child(20) { height: 75%; }
.viz-bar:nth-child(21) { height: 30%; }
.viz-bar:nth-child(22) { height: 65%; }
.viz-bar:nth-child(23) { height: 50%; }
.viz-bar:nth-child(24) { height: 45%; }

@keyframes vizWave {
  0%, 100% { transform: scaleY(0.5); opacity: 0.5; }
  50% { transform: scaleY(1); opacity: 1; }
}

.mood-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
}

.mood-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.mood-romance { background: #6b46c1; box-shadow: 0 0 6px rgba(107, 70, 193, 0.5); }
.mood-calm { background: #06b6d4; box-shadow: 0 0 6px rgba(6, 182, 212, 0.5); }
.mood-energy { background: #f59e0b; box-shadow: 0 0 6px rgba(245, 158, 11, 0.5); }

.mood-sep { color: #475569; }

.hero-date {
  text-align: right;
  font-size: 13px;
  color: #64748b;
  margin-top: 12px;
  padding-right: 8px;
}

@media (max-width: 900px) {
  .hero-glass {
    flex-direction: column;
    padding: 28px 24px;
  }
  .hero-title {
    font-size: 24px;
  }
  .hero-right {
    min-width: auto;
    width: 100%;
  }
  .sound-visualizer {
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .hero-actions {
    flex-direction: column;
  }
  .hero-btn {
    justify-content: center;
  }
}
</style>
