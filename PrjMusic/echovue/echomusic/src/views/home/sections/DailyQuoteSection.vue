<script setup lang="ts">
import { computed } from 'vue'
import { useTypewriter } from '@/composables/useTypewriter'

const quotes = [
  { text: '我听见回声，来自山谷和心间', song: '生如夏花', artist: '朴树' },
  { text: '如果天黑之前来得及，我要忘了你的眼睛', song: '南山南', artist: '马頔' },
  { text: '青春如同奔流的江河，一去不回来不及道别', song: '老男孩', artist: '筷子兄弟' },
  { text: '我想要更好更圆的月亮，想要未知的疯狂', song: '奇妙能力歌', artist: '陈粒' },
  { text: '岁月是一场有去无回的旅行，好的坏的都是风景', song: '岁月神偷', artist: '金玟岐' },
]

const todayQuote = computed(() => {
  const day = new Date().getDate()
  return quotes[day % quotes.length] ?? quotes[0]!
})

const { displayText: typedText, isDone } = useTypewriter(todayQuote.value.text, {
  speed: 80,
  delay: 800
})
</script>

<template>
  <section class="quote-section">
    <div class="quote-glass">
      <div class="quote-decoration">
        <div class="glow-orb orb-1" />
        <div class="glow-orb orb-2" />
      </div>
      <div class="quote-content">
        <div class="quote-mark-large">"</div>
        <p class="quote-text">
          {{ typedText }}<span v-if="!isDone" class="quote-cursor">|</span>
        </p>
        <div class="quote-source">
          <span class="source-line" />
          <span class="source-text">《{{ todayQuote.song }}》· {{ todayQuote.artist }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.quote-section {
  padding: 32px 0;
  position: relative;
  z-index: 2;
}

.quote-glass {
  position: relative;
  padding: 48px 40px;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.06) 0%, rgba(236, 72, 153, 0.03) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 24px;
  overflow: hidden;
  text-align: center;
}

.quote-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.15;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: #6b46c1;
  top: -100px;
  left: 10%;
}

.orb-2 {
  width: 250px;
  height: 250px;
  background: #ec4899;
  bottom: -80px;
  right: 10%;
}

.quote-content {
  position: relative;
  z-index: 1;
}

.quote-mark-large {
  font-size: 80px;
  line-height: 1;
  color: rgba(107, 70, 193, 0.3);
  font-family: Georgia, serif;
  margin-bottom: -20px;
}

.quote-text {
  font-size: 22px;
  font-weight: 500;
  color: #e2e8f0;
  line-height: 1.8;
  min-height: 40px;
  font-style: italic;
}

.quote-cursor {
  color: #ec4899;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.quote-source {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 24px;
}

.source-line {
  width: 30px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(236, 72, 153, 0.5));
}

.source-text {
  font-size: 14px;
  color: #64748b;
}

@media (max-width: 640px) {
  .quote-glass {
    padding: 32px 24px;
  }
  .quote-text {
    font-size: 18px;
  }
  .quote-mark-large {
    font-size: 60px;
  }
}
</style>
