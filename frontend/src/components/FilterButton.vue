<template>
  <div class="filter-button" :class="{ 'as-input': asInput }">
    <slot name="prefix" />
    <input
      v-if="asInput"
      :value="modelValue"
      :placeholder="placeholder"
      class="filter-input"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @keydown.enter="$emit('enter')"
    />
    <span v-else class="filter-text"><slot /></span>
    <slot name="suffix" />
  </div>
</template>

<script setup lang="ts">
interface Props {
  asInput?: boolean
  modelValue?: string
  placeholder?: string
}
defineProps<Props>()
defineEmits<{
  'update:modelValue': [value: string]
  enter: []
}>()
</script>

<style scoped>
.filter-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0 14px;
  height: 36px;
  background-color: var(--button-default-light);
  color: var(--text-secondary);
  font-family: var(--font-body);
  font-size: 14px;
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  cursor: pointer;
}
.filter-button.as-input {
  cursor: text;
  width: 100%;
}
.filter-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}
.filter-input::placeholder {
  color: var(--text-tertiary);
}
</style>
