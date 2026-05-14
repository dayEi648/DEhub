<template>
  <div class="empty-state">
    <div class="empty-icon">📭</div>
    <p class="empty-text">{{ description }}</p>
    <PillLink v-if="actionText" :to="actionTo" @click="$emit('action')">
      {{ actionText }}
    </PillLink>
  </div>
</template>

<script setup lang="ts">
import PillLink from './PillLink.vue'

interface Props {
  description: string
  actionText?: string
  actionTo?: string
}
defineProps<Props>()
defineEmits<{
  action: []
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 24px;
  text-align: center;
}
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}
.empty-text {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}
</style>
