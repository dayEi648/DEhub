<template>
  <button
    :type="type"
    :disabled="disabled"
    class="primary-button"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
interface Props {
  type?: 'button' | 'submit'
  disabled?: boolean
}
withDefaults(defineProps<Props>(), {
  type: 'button',
  disabled: false
})
defineEmits<{
  click: [event: MouseEvent]
}>()
</script>

<style scoped>
.primary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 15px;
  font-family: var(--font-body);
  font-size: 17px;
  font-weight: 400;
  line-height: 2.41;
  color: var(--text-white);
  background-color: var(--apple-blue);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.primary-button:hover:not(:disabled) {
  background-color: var(--apple-blue-hover);
}
.primary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
