<template>
  <div class="links-page">
    <div class="container">
      <h1 class="page-title">子网站</h1>
      <p class="page-desc">该功能正在开发中，敬请期待。</p>
      <div class="links-grid">
        <Card v-for="i in 3" :key="i" class="link-card">
          <div class="link-placeholder">
            <h3 class="link-name">项目名称 {{ i }}</h3>
            <p class="link-desc">项目描述将显示在这里</p>
            <span class="link-url">https://example.com</span>
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Card from '@/components/Card.vue'
</script>

<style scoped>
.links-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.page-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 32px;
}
.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}
.link-card {
  padding: 32px;
  opacity: 0.6;
}
.link-placeholder {
  text-align: center;
}
.link-name {
  font-size: 21px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.link-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}
.link-url {
  font-size: 12px;
  color: var(--link-blue);
}
</style>
