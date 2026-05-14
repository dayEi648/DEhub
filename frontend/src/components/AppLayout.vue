<template>
  <div class="app-layout">
    <GlobalNav />
    <main class="main-content">
      <router-view />
    </main>
    <GlobalFooter />
    <ToastContainer />
    <div v-if="uiStore.globalLoading" class="global-loading">
      <LoadingSpinner />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import GlobalNav from './GlobalNav.vue'
import GlobalFooter from './GlobalFooter.vue'
import ToastContainer from './ToastContainer.vue'
import LoadingSpinner from './LoadingSpinner.vue'

const uiStore = useUiStore()
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}
.main-content {
  padding-top: 48px;
  min-height: calc(100vh - 48px);
}
.global-loading {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9997;
}
</style>
