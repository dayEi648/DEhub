<script setup lang="ts">
import HomeHeader from './HomeHeader.vue'
import WaveBackground from '@/components/WaveBackground/WaveBackground.vue'

const props = defineProps<{
  searchKeyword: string
}>()

const emit = defineEmits<{
  (e: 'update:searchKeyword', val: string): void
  (e: 'search'): void
  (e: 'goAdmin'): void
  (e: 'goProfile'): void
  (e: 'logout'): void
}>()
</script>

<template>
  <div class="home-layout">
    <WaveBackground />
    <HomeHeader
      :search-keyword="searchKeyword"
      @update:search-keyword="$emit('update:searchKeyword', $event)"
      @search="$emit('search')"
      @go-admin="$emit('goAdmin')"
      @go-profile="$emit('goProfile')"
      @logout="$emit('logout')"
    />

    <div class="home-main">
      <slot />
    </div>

    <footer class="home-footer">
      <!-- 声波分隔线 -->
      <div class="footer-wave-divider">
        <svg viewBox="0 0 1440 60" preserveAspectRatio="none" class="wave-svg">
          <path
            d="M0,30 C200,60 400,0 600,30 C800,60 1000,0 1200,30 C1340,50 1400,20 1440,30 L1440,60 L0,60 Z"
            fill="rgba(107, 70, 193, 0.08)"
          />
          <path
            d="M0,40 C300,20 500,50 700,35 C900,20 1100,50 1300,30 C1380,20 1420,35 1440,40 L1440,60 L0,60 Z"
            fill="rgba(236, 72, 153, 0.05)"
          />
        </svg>
      </div>
      <div class="footer-inner">
        <div class="footer-top">
          <div class="footer-brand">
            <div class="footer-logo">
              <div class="sound-wave">
                <span v-for="i in 4" :key="i" class="wave-bar" />
              </div>
            </div>
            <span class="footer-name">EchoMemory</span>
          </div>
          <div class="footer-link-groups">
            <div class="link-group">
              <h4>关于</h4>
              <a href="javascript:;">关于我们</a>
              <a href="javascript:;">团队介绍</a>
              <a href="javascript:;">联系我们</a>
            </div>
            <div class="link-group">
              <h4>社区</h4>
              <a href="javascript:;">用户协议</a>
              <a href="javascript:;">社区规范</a>
              <a href="javascript:;">帮助中心</a>
            </div>
            <div class="link-group">
              <h4>法律</h4>
              <a href="javascript:;">隐私政策</a>
              <a href="javascript:;">版权声明</a>
              <a href="javascript:;">免责声明</a>
            </div>
          </div>
        </div>
        <div class="footer-quote">
          "Music is the echo of memory"
        </div>
        <div class="footer-copy">
          © 2026 EchoMemory 回声记忆. All rights reserved.
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.home-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #1e1b2e 100%);
  background-attachment: fixed;
}

.home-main {
  padding-top: 72px;
  min-height: calc(100vh - 72px - 160px);
}

/* Footer */
.home-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(15, 20, 25, 0.6);
  backdrop-filter: blur(10px);
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-logo {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-logo .sound-wave {
  display: flex;
  align-items: center;
  gap: 1.5px;
  height: 14px;
}

.footer-logo .wave-bar {
  width: 2px;
  background: white;
  border-radius: 1px;
}

.footer-logo .wave-bar:nth-child(1) { height: 6px; }
.footer-logo .wave-bar:nth-child(2) { height: 10px; }
.footer-logo .wave-bar:nth-child(3) { height: 7px; }
.footer-logo .wave-bar:nth-child(4) { height: 12px; }

.footer-name {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-links a {
  color: #64748b;
  font-size: 13px;
  text-decoration: none;
  transition: color 0.3s ease;
}

.footer-links a:hover {
  color: #a78bfa;
}

.footer-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  flex-wrap: wrap;
  gap: 32px;
}

.footer-link-groups {
  display: flex;
  gap: 48px;
  flex-wrap: wrap;
}

.link-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.link-group h4 {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.link-group a {
  color: #64748b;
  font-size: 13px;
  text-decoration: none;
  transition: color 0.3s ease;
}

.link-group a:hover {
  color: #a78bfa;
}

.footer-copy {
  color: #475569;
  font-size: 12px;
}
</style>
