<template>
  <div class="chat-page">
    <ChatSidebar />
    <div class="chat-main">
      <div class="chat-toolbar">
        <button
          v-if="uiStore.isChatSidebarCollapsed"
          class="sidebar-toggle"
          title="展开侧边栏"
          @click="uiStore.toggleChatSidebar()"
        >
          ☰
        </button>
      </div>
      <div ref="messageListRef" class="message-list" @scroll="handleScroll">
        <div v-if="chatStore.currentMessages.length === 0" class="chat-welcome">
          <h1 class="welcome-title">DE hub AI</h1>
          <p class="welcome-subtitle">有什么可以帮你的？</p>
        </div>
        <ChatMessage
          v-for="(msg, index) in chatStore.currentMessages"
          :key="msg.id + '-' + index"
          :message="msg"
        />
      </div>
      <div
        v-if="showScrollToBottom"
        class="scroll-to-bottom"
        @click="scrollToBottom(true)"
      >
        新消息 ↓
      </div>
      <ChatInput @send="handleSend" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import ChatSidebar from '@/components/ChatSidebar.vue'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'

const chatStore = useChatStore()
const uiStore = useUiStore()
const messageListRef = ref<HTMLElement>()
const showScrollToBottom = ref(false)
const isUserScrolledUp = ref(false)

function isNearBottom(el: HTMLElement) {
  return el.scrollTop + el.clientHeight >= el.scrollHeight - 50
}

function scrollToBottom(smooth = true) {
  if (messageListRef.value) {
    messageListRef.value.scrollTo({
      top: messageListRef.value.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    })
  }
  showScrollToBottom.value = false
  isUserScrolledUp.value = false
}

function handleScroll() {
  if (!messageListRef.value) return
  const nearBottom = isNearBottom(messageListRef.value)
  isUserScrolledUp.value = !nearBottom
  if (nearBottom) {
    showScrollToBottom.value = false
  }
}

async function handleSend(payload: { content: string }) {
  await chatStore.sendMessage(
    payload.content,
    chatStore.currentConversationId || undefined
  )
  // Auto-scroll on send
  isUserScrolledUp.value = false
  showScrollToBottom.value = false
}

// Auto-scroll when new messages arrive, unless user has scrolled up
watch(
  () => chatStore.currentMessages.length,
  async () => {
    await nextTick()
    if (!isUserScrolledUp.value) {
      scrollToBottom(false)
    } else {
      showScrollToBottom.value = true
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
  position: relative;
}
.chat-toolbar {
  padding: 8px 16px 0;
  display: flex;
  align-items: center;
}
.sidebar-toggle {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.48);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  transition: color 0.2s ease;
}
.sidebar-toggle:hover {
  color: var(--text-white);
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
.scroll-to-bottom {
  position: absolute;
  bottom: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  background: var(--dark-surface-1);
  color: var(--text-white);
  font-size: 13px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  z-index: 10;
  animation: fadeIn 0.2s ease;
}
</style>
