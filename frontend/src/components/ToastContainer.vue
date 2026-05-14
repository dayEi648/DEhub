<template>
  <Teleport to="body">
    <div class="toast-container">
      <Toast
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        :toast="toast"
      />
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import Toast from './Toast.vue'

const uiStore = useUiStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 60px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast-container > * {
  pointer-events: auto;
}
</style>
