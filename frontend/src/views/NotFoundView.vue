<template>
  <div class="not-found">
    <h1 class="not-found-code">404</h1>
    <p class="not-found-text">页面不存在</p>
    <PillLink to="/">返回首页</PillLink>
  </div>
</template>

<script setup lang="ts">
import PillLink from '@/components/PillLink.vue'
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  background: var(--bg-black);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.not-found-code {
  font-family: var(--font-display);
  font-size: 56px;
  font-weight: 600;
  line-height: 1.07;
  color: var(--text-white);
  margin-bottom: 12px;
}
.not-found-text {
  font-size: 21px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 24px;
}
</style>
