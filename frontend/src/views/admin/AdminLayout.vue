<template>
  <div class="admin-layout">
    <AdminNav />
    <div class="admin-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import AdminNav from './AdminNav.vue'
</script>

<style scoped>
.admin-layout {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
}
.admin-content {
  padding: 32px 0;
}
</style>
