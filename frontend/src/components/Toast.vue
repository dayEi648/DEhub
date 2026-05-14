<template>
  <div class="toast" :class="toast.type">
    <span class="toast-message">{{ toast.message }}</span>
  </div>
</template>

<script setup lang="ts">
import type { ToastItem } from '@/stores/ui'

interface Props {
  toast: ToastItem
}
defineProps<Props>()
</script>

<style scoped>
.toast {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: var(--text-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  animation: slideDown 0.3s ease;
}
.toast.success {
  border-left: 4px solid var(--apple-blue);
}
.toast.error {
  border-left: 4px solid var(--error-red);
}
.toast.warning {
  border-left: 4px solid var(--warning-orange);
}
.toast-message {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-primary);
}
</style>
