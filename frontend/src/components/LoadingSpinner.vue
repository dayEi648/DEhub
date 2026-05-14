<template>
  <div class="spinner" :style="spinnerStyle">
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-dasharray="31.42"
        stroke-dashoffset="10"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  size?: number
}
const props = withDefaults(defineProps<Props>(), {
  size: 40
})

const spinnerStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`
}))
</script>

<style scoped>
.spinner {
  color: var(--apple-blue);
  animation: spin 1s linear infinite;
}
.spinner svg {
  width: 100%;
  height: 100%;
}
</style>
