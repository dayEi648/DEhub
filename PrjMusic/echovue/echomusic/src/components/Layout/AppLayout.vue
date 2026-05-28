<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

defineProps<{
  title: string
  breadcrumb?: string[]
}>()
</script>

<template>
  <div class="layout">
    <Sidebar />

    <div class="main-container">
      <Header :title="title" :breadcrumb="breadcrumb" />

      <main class="main-content">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #1e1b2e 100%);
  background-attachment: fixed;
}

.main-container {
  margin-left: 220px;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #1e1b2e 100%);
  background-attachment: fixed;
}

.main-content {
  padding: 24px 28px;
  background: transparent;
}
</style>
