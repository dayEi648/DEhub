<template>
  <aside class="chat-sidebar" :class="{ open: uiStore.isMobileMenuOpen }">
    <div class="sidebar-header">
      <PrimaryButton class="new-chat-btn" @click="startNewChat">新建对话</PrimaryButton>
    </div>
    <div class="conversation-list">
      <div
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        class="conversation-item"
        :class="{ active: chatStore.currentConversationId === conv.id }"
        @click="selectConversation(conv.id)"
      >
        <span class="conv-title">{{ conv.title }}</span>
        <span class="conv-time">{{ formatDate(conv.created_at) }}</span>
        <button class="delete-btn" @click.stop="chatStore.deleteConversation(conv.id)">🗑</button>
      </div>
      <div v-if="chatStore.conversations.length === 0" class="empty-conversations">
        暂无历史对话
      </div>
    </div>
  </aside>
  <div v-if="uiStore.isMobileMenuOpen" class="sidebar-backdrop" @click="uiStore.isMobileMenuOpen = false" />
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import PrimaryButton from './PrimaryButton.vue'

const chatStore = useChatStore()
const uiStore = useUiStore()

onMounted(() => {
  chatStore.fetchConversations()
})

function startNewChat() {
  chatStore.currentConversationId = null
  chatStore.currentMessages = []
  uiStore.isMobileMenuOpen = false
}

function selectConversation(id: number) {
  chatStore.fetchMessages(id)
  uiStore.isMobileMenuOpen = false
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.chat-sidebar {
  width: 280px;
  height: 100%;
  background: var(--text-primary);
  border-right: 1px solid var(--dark-surface-3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--dark-surface-3);
}
.new-chat-btn {
  width: 100%;
}
.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.conversation-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  position: relative;
}
.conversation-item:hover {
  background: var(--dark-surface-2);
}
.conversation-item.active {
  background: var(--dark-surface-3);
}
.conv-title {
  font-size: 14px;
  color: var(--text-white);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.48);
}
.delete-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  font-size: 12px;
  opacity: 0;
  cursor: pointer;
}
.conversation-item:hover .delete-btn {
  opacity: 1;
}
.empty-conversations {
  padding: 40px 16px;
  text-align: center;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.48);
}
.sidebar-backdrop {
  display: none;
}

@media (max-width: 640px) {
  .chat-sidebar {
    position: fixed;
    left: 0;
    top: 48px;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  .chat-sidebar.open {
    transform: translateX(0);
  }
  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 48px 0 0 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}
</style>
