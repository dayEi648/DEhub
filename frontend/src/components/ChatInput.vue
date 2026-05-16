<template>
  <div class="chat-input-area">
    <div class="input-row">
      <textarea
        ref="textareaRef"
        v-model="content"
        class="message-input"
        rows="1"
        placeholder="输入消息..."
        @keydown="handleKeydown"
        @input="autoResize"
      />
      <button
        class="send-btn"
        :disabled="chatStore.isLoading || !content.trim()"
        @click="send"
      >
        <span v-if="chatStore.isLoading">⋯</span>
        <span v-else>→</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const content = ref('')
const textareaRef = ref<HTMLTextAreaElement>()

const emit = defineEmits<{
  send: [payload: { content: string }]
}>()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function autoResize(e: Event) {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 140) + 'px'
}

function send() {
  if (!content.value.trim() || chatStore.isLoading) return
  emit('send', { content: content.value.trim() })
  content.value = ''
  // Reset textarea height
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}
</script>

<style scoped>
.chat-input-area {
  padding: 16px 24px;
  background: var(--bg-black);
  border-top: 1px solid var(--dark-surface-3);
}
.input-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
.message-input {
  flex: 1;
  padding: 12px 16px;
  font-size: 15px;
  color: var(--text-white);
  background: var(--dark-surface-2);
  border: none;
  border-radius: var(--radius-xl);
  resize: none;
  outline: none;
  min-height: 44px;
  max-height: 140px;
}
.message-input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}
.send-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--apple-blue);
  color: var(--text-white);
  border: none;
  border-radius: 50%;
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
}
.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
