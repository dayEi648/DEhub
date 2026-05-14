<template>
  <div class="avatar" :style="{ width: size + 'px', height: size + 'px' }">
    <img v-if="src" :src="src" :alt="name" class="avatar-img" />
    <span v-else class="avatar-text">{{ initial }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  src?: string | null
  name?: string
  size?: number
}
const props = withDefaults(defineProps<Props>(), {
  src: null,
  name: '',
  size: 40
})

const initial = computed(() => {
  return props.name?.charAt(0)?.toUpperCase() || '?'
})
</script>

<style scoped>
.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background-color: var(--dark-surface-1);
  flex-shrink: 0;
}
.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-text {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-white);
}
</style>
