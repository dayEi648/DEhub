<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const isVisible = computed(() => props.visible)
</script>

<template>
  <Transition name="loading-fade">
    <div v-if="isVisible" class="page-loading-overlay">
      <div class="loading-container">
        <!-- 音频波形动画 -->
        <div class="waveform">
          <div v-for="n in 12" :key="n" class="wave-bar" :style="{ '--delay': `${(n - 1) * 0.1}s` }"></div>
        </div>

        <!-- 品牌文字 -->
        <div class="brand-text">
          <span class="echo">Echo</span>
          <span class="memory">Memory</span>
        </div>

        <!-- 加载提示 -->
        <div class="loading-text">正在加载音乐世界...</div>
      </div>

      <!-- 背景装饰 -->
      <div class="bg-decoration bg-decoration-1"></div>
      <div class="bg-decoration bg-decoration-2"></div>
      <div class="bg-decoration bg-decoration-3"></div>
    </div>
  </Transition>
</template>

<style scoped>
.page-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 40%, #2d1b4e 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  overflow: hidden;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  z-index: 1;
}

/* 音频波形动画 */
.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 80px;
}

.wave-bar {
  width: 6px;
  height: 100%;
  background: linear-gradient(180deg, #ec4899 0%, #6b46c1 50%, #8b5cf6 100%);
  border-radius: 3px;
  animation: wave-jump 0.8s ease-in-out infinite;
  animation-delay: var(--delay);
  box-shadow:
    0 0 10px rgba(236, 72, 153, 0.5),
    0 0 20px rgba(107, 70, 193, 0.3);
}

@keyframes wave-jump {
  0%, 100% {
    transform: scaleY(0.3);
    opacity: 0.6;
  }
  50% {
    transform: scaleY(1);
    opacity: 1;
  }
}

/* 品牌文字 */
.brand-text {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 2px;
  display: flex;
  gap: 4px;
}

.brand-text .echo {
  background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-text .memory {
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 加载提示文字 */
.loading-text {
  font-size: 14px;
  color: rgba(148, 163, 184, 0.8);
  letter-spacing: 1px;
  animation: text-pulse 1.5s ease-in-out infinite;
}

@keyframes text-pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

/* 背景装饰圆圈 */
.bg-decoration {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
  filter: blur(60px);
  animation: float 6s ease-in-out infinite;
}

.bg-decoration-1 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #6b46c1 0%, #8b5cf6 100%);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.bg-decoration-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #ec4899 0%, #f472b6 100%);
  bottom: -50px;
  left: -50px;
  animation-delay: -2s;
}

.bg-decoration-3 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation-delay: -4s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.05);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.95);
  }
}

/* 淡入淡出过渡动画 */
.loading-fade-enter-active {
  transition: none;
}
.loading-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.loading-fade-enter-from {
  opacity: 0;
  transform: scale(1.02);
}

.loading-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

.loading-fade-enter-to,
.loading-fade-leave-from {
  opacity: 1;
  transform: scale(1);
}
</style>
