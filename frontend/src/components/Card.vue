<template>
  <div class="card" :class="{ dark }">
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  dark?: boolean
}
withDefaults(defineProps<Props>(), {
  dark: false
})
</script>

<style scoped>
.card {
  background-color: var(--bg-gray);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.card.dark {
  background-color: var(--dark-surface-1);
}
</style>
