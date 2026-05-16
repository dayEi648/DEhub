<template>
  <div class="chat-message" :class="message.role">
    <template v-if="message.role === 'system'">
      <span class="system-text">{{ message.content }}</span>
    </template>
    <template v-else-if="message.role === 'assistant'">
      <div class="assistant-row">
        <div class="ai-avatar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8" y2="16" stroke-linecap="round" stroke-width="2.5" />
            <line x1="16" y1="16" x2="16" y2="16" stroke-linecap="round" stroke-width="2.5" />
          </svg>
        </div>
        <div class="assistant-content">
          <div class="message-bubble">
            <div v-if="isTyping" class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <MarkdownRenderer v-else :content="message.content" />
          </div>
          <span v-if="!isTyping" class="message-time">{{ formatTime(message.created_at) }}</span>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="message-bubble">
        {{ message.content }}
      </div>
      <span class="message-time">{{ formatTime(message.created_at) }}</span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { MessageResponse } from '@/types'
import { useChatStore } from '@/stores/chat'
import MarkdownRenderer from './MarkdownRenderer.vue'

interface Props {
  message: MessageResponse
}
const props = defineProps<Props>()

const chatStore = useChatStore()

const isTyping = computed(() => {
  return (
    props.message.role === 'assistant' &&
    props.message.content === '' &&
    chatStore.isLoading
  )
})

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
.chat-message.system {
  align-items: center;
}

.assistant-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.ai-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  margin-top: 2px;
}
.ai-avatar svg {
  width: 16px;
  height: 16px;
}
.assistant-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: calc(100% - 38px);
}

.message-bubble {
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.6;
  word-break: break-word;
}
.chat-message.user .message-bubble {
  background: var(--apple-blue);
  color: var(--text-white);
  border-radius: 18px 18px 4px 18px;
  max-width: 70%;
}
.chat-message.assistant .message-bubble {
  background: var(--dark-surface-1);
  color: var(--text-white);
  border-radius: 4px 18px 18px 18px;
}
.chat-message.assistant .message-bubble :deep(.markdown-body) {
  color: var(--text-white);
}
.chat-message.assistant .message-bubble :deep(.markdown-body) blockquote {
  color: rgba(255, 255, 255, 0.6);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 20px;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  animation: typingBounce 1.4s infinite ease-in-out both;
}
.typing-indicator span:nth-child(1) {
  animation-delay: 0s;
}
.typing-indicator span:nth-child(2) {
  animation-delay: 0.16s;
}
.typing-indicator span:nth-child(3) {
  animation-delay: 0.32s;
}

@keyframes typingBounce {
  0%, 100% {
    transform: translateY(0) scale(0.6);
    opacity: 0.3;
  }
  50% {
    transform: translateY(-6px) scale(1.1);
    opacity: 1;
  }
}

.system-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.48);
  padding: 4px 0;
}
.message-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}
.chat-message.user .message-time {
  text-align: right;
}
.chat-message.assistant .message-time {
  text-align: left;
}
</style>
