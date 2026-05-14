<template>
  <div class="chat-page">
    <ChatSidebar />
    <div class="chat-main">
      <div ref="messageListRef" class="message-list">
        <div v-if="chatStore.currentMessages.length === 0" class="chat-welcome">
          <h1 class="welcome-title">DE hub AI</h1>
          <p class="welcome-subtitle">有什么可以帮你的？</p>
        </div>
        <ChatMessage
          v-for="(msg, index) in chatStore.currentMessages"
          :key="msg.id + '-' + index"
          :message="msg"
          :is-streaming="chatStore.isStreaming && index === chatStore.currentMessages.length - 1 && msg.role === 'assistant'"
        />
      </div>
      <ChatInput @send="handleSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'

const chatStore = useChatStore()
const messageListRef = ref<HTMLElement>()

function handleSend(payload: { content: string; systemPrompt?: string }) {
  chatStore.sendMessage(payload.content, chatStore.currentConversationId || undefined, payload.systemPrompt)
}

watch(
  () => chatStore.currentMessages.length,
  async () => {
    await nextTick()
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  }
)
</script>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - 48px);
  background: var(--bg-black);
}
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.welcome-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 8px;
}
.welcome-subtitle {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.48);
}
</style>
