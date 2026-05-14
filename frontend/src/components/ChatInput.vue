<template>
  <div class="chat-input-area">
    <div class="system-prompt-toggle" @click="showSystem = !showSystem">
      {{ showSystem ? '收起' : '展开' }}系统提示词（可选）
    </div>
    <textarea
      v-if="showSystem"
      v-model="systemPrompt"
      class="system-input"
      rows="1"
      placeholder="系统提示词..."
    />
    <div class="input-row">
      <textarea
        v-model="content"
        class="message-input"
        rows="1"
        placeholder="输入消息..."
        @keydown="handleKeydown"
        @input="autoResize"
      />
      <button
        class="send-btn"
        :disabled="!content.trim() || chatStore.isStreaming"
        @click="send"
      >
        {{ chatStore.isStreaming ? '⏹' : '→' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const content = ref('')
const systemPrompt = ref('')
const showSystem = ref(false)

const emit = defineEmits<{
  send: [payload: { content: string; systemPrompt?: string }]
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
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

function send() {
  if (!content.value.trim() || chatStore.isStreaming) return
  emit('send', {
    content: content.value.trim(),
    systemPrompt: systemPrompt.value || undefined
  })
  content.value = ''
}
</script>

<style scoped>
.chat-input-area {
  padding: 16px 24px;
  background: var(--bg-black);
  border-top: 1px solid var(--dark-surface-3);
}
.system-prompt-toggle {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.48);
  cursor: pointer;
  margin-bottom: 8px;
}
.system-input {
  width: 100%;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-white);
  background: var(--dark-surface-2);
  border: none;
  border-radius: var(--radius-md);
  margin-bottom: 8px;
  resize: none;
  outline: none;
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
  max-height: 120px;
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
