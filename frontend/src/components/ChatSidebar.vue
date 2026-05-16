<template>
  <aside class="chat-sidebar" :class="{ open: uiStore.isMobileMenuOpen, collapsed: uiStore.isChatSidebarCollapsed }">
    <div class="sidebar-header">
      <PrimaryButton class="new-chat-btn" @click="startNewChat">新建对话</PrimaryButton>
      <button
        class="collapse-btn"
        title="收起侧边栏"
        @click="uiStore.isChatSidebarCollapsed = true"
      >
        «
      </button>
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
        <span class="conv-time">{{ formatDate(conv.updated_at) }}</span>
        <button class="delete-btn" @click.stop="confirmDelete(conv.id)">🗑</button>
      </div>
      <div v-if="chatStore.conversations.length === 0" class="empty-conversations">
        暂无历史对话
      </div>
    </div>
  </aside>
  <div v-if="uiStore.isMobileMenuOpen" class="sidebar-backdrop" @click="uiStore.isMobileMenuOpen = false" />

  <Modal v-model="showDeleteModal" title="确认删除">
    <p>确定要删除这个对话吗？此操作无法撤销。</p>
    <template #footer>
      <button class="action-link danger" @click="executeDelete">确认删除</button>
      <PillLink @click="showDeleteModal = false">取消</PillLink>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'
import PrimaryButton from './PrimaryButton.vue'
import PillLink from './PillLink.vue'
import Modal from './Modal.vue'

const chatStore = useChatStore()
const uiStore = useUiStore()

const showDeleteModal = ref(false)
const pendingDeleteId = ref<number | null>(null)

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

function confirmDelete(id: number) {
  pendingDeleteId.value = id
  showDeleteModal.value = true
}

function executeDelete() {
  if (pendingDeleteId.value !== null) {
    showDeleteModal.value = false
    chatStore.deleteConversation(pendingDeleteId.value)
    pendingDeleteId.value = null
  }
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
  transition: width 0.3s ease, opacity 0.3s ease;
  flex-shrink: 0;
}
.chat-sidebar.collapsed {
  width: 0;
  opacity: 0;
  padding: 0;
  border: none;
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--dark-surface-3);
  display: flex;
  align-items: center;
  gap: 8px;
}
.collapse-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.48);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
  transition: color 0.2s ease;
}
.collapse-btn:hover {
  color: var(--text-white);
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
.action-link {
  background: none;
  border: none;
  color: var(--apple-blue);
  font-size: 15px;
  cursor: pointer;
  padding: 0;
}
.action-link.danger {
  color: var(--error-red);
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
    width: 280px;
    opacity: 1;
  }
  .chat-sidebar.open {
    transform: translateX(0);
  }
  .chat-sidebar.collapsed {
    width: 280px;
    opacity: 1;
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
