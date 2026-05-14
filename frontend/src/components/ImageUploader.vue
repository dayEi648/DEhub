<template>
  <div class="image-uploader" :style="{ width: size + 'px', height: size + 'px' }" @click="triggerFileInput">
    <Avatar :src="previewUrl" :name="name" :size="size" />
    <div class="upload-overlay">
      <span class="upload-icon">📷</span>
    </div>
    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      hidden
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useUiStore } from '@/stores/ui'
import Avatar from './Avatar.vue'

interface Props {
  previewUrl?: string | null
  name?: string
  size?: number
  accept?: string
  maxSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  previewUrl: null,
  name: '',
  size: 160,
  accept: 'image/*',
  maxSize: 5 * 1024 * 1024
})

const emit = defineEmits<{
  select: [file: File]
}>()

const uiStore = useUiStore()
const fileInput = ref<HTMLInputElement>()

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > props.maxSize) {
    uiStore.showToast(`文件大小不能超过 ${props.maxSize / 1024 / 1024}MB`, 'error')
    return
  }
  emit('select', file)
}
</script>

<style scoped>
.image-uploader {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
}
.upload-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.2s ease;
  border-radius: 50%;
}
.image-uploader:hover .upload-overlay {
  opacity: 1;
}
.upload-icon {
  font-size: 24px;
  color: var(--text-white);
}
</style>
