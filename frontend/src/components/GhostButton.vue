<template>
  <button
    class="ghost-button"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<style scoped>
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 15px;
  font-family: var(--font-body);
  font-size: 17px;
  font-weight: 400;
  line-height: 2.41;
  color: var(--text-white);
  background-color: transparent;
  border: 1px solid var(--text-white);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}
.ghost-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
</style>
