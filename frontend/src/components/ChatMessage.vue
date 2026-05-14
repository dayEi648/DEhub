<template>
  <div class="chat-message" :class="message.role">
    <div class="message-bubble">
      <MarkdownRenderer v-if="message.role === 'assistant'" :content="message.content" />
      <template v-else>{{ message.content }}</template>
      <span v-if="isStreaming" class="cursor">|</span>
    </div>
    <span class="message-time">{{ formatTime(message.created_at) }}</span>
  </div>
</template>

<script setup lang="ts">
import type { MessageResponse } from '@/types'
import MarkdownRenderer from './MarkdownRenderer.vue'

interface Props {
  message: MessageResponse
  isStreaming?: boolean
}
defineProps<Props>()

function formatTime(date: string) {
  return new Date(date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.chat-message.user {
  align-items: flex-end;
}
.chat-message.assistant {
  align-items: flex-start;
}
.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}
.chat-message.user .message-bubble {
  background: var(--apple-blue);
  color: var(--text-white);
  border-radius: 18px 18px 4px 18px;
}
.chat-message.assistant .message-bubble {
  background: var(--dark-surface-1);
  color: var(--text-white);
  border-radius: 4px 18px 18px 18px;
}
.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}
.cursor {
  display: inline-block;
  color: var(--apple-blue);
  animation: blink 1s infinite;
  margin-left: 2px;
}
</style>
