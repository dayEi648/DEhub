<template>
  <div class="tag-input">
    <div class="tag-list">
      <span v-for="(tag, index) in modelValue" :key="tag + index" class="tag">
        {{ tag }}
        <button class="tag-remove" @click="removeTag(index)">×</button>
      </span>
    </div>
    <input
      v-model="inputValue"
      class="tag-input-field"
      placeholder="输入标签，按回车或逗号添加"
      @keydown.enter.prevent="addTag"
      @keydown.comma.prevent="addTag"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  modelValue: string[]
}
const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const inputValue = ref('')

function addTag() {
  const raw = inputValue.value.trim()
  if (!raw) return
  const tags = raw.split(',').map((t) => t.trim()).filter((t) => t && !props.modelValue.includes(t))
  if (tags.length) {
    emit('update:modelValue', [...props.modelValue, ...tags])
  }
  inputValue.value = ''
}

function removeTag(index: number) {
  const newTags = [...props.modelValue]
  newTags.splice(index, 1)
  emit('update:modelValue', newTags)
}
</script>

<style scoped>
.tag-input {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-sm);
}
.tag-remove {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
}
.tag-remove:hover {
  color: var(--error-red);
}
.tag-input-field {
  padding: 10px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
}
.tag-input-field:focus {
  border-color: var(--apple-blue);
}
</style>
