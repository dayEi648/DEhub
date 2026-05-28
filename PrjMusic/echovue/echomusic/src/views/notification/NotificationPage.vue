<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  ChatLineRound,
  Message,
  Notification as NotificationIcon,
  Check,
  Loading,
  ArrowLeft
} from '@element-plus/icons-vue'
import { getNotifications, readNotifications, readAllNotifications } from '@/api/notification'
import { getConversations } from '@/api/privateMessage'
import type { NotificationVO, NotificationPageQuery } from '@/types/notification'
import type { ConversationVO } from '@/types/privateMessage'

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: 'private', label: '私信', icon: ChatLineRound },
  { key: 'mention', label: '@我的', icon: ChatDotRound },
  { key: 'notify', label: '通知', icon: NotificationIcon },
  { key: 'comment', label: '评论', icon: Message }
]

const activeTab = ref(route.query.tab as string || 'private')

watch(() => route.query.tab, (val) => {
  if (val && tabs.some(t => t.key === val)) {
    activeTab.value = val as string
  }
})

function switchTab(key: string) {
  activeTab.value = key
  router.replace({ query: { ...route.query, tab: key } })
  loadData()
}

// ========== 通知列表 ==========
const notifications = ref<NotificationVO[]>([])
const pageNum = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const hasMore = ref(true)

// ========== 私信会话 ==========
const conversations = ref<ConversationVO[]>([])
const convLoading = ref(false)

async function loadData() {
  if (activeTab.value === 'private') {
    await loadConversations()
  } else {
    pageNum.value = 1
    notifications.value = []
    hasMore.value = true
    await loadNotifications()
  }
}

async function loadNotifications() {
  if (loading.value) return
  loading.value = true
  try {
    const query: NotificationPageQuery = {
      pageNum: pageNum.value,
      pageSize: pageSize.value,
      category: activeTab.value
    }
    const res = await getNotifications(query)
    if (pageNum.value === 1) {
      notifications.value = res.records
    } else {
      notifications.value.push(...res.records)
    }
    total.value = res.total
    hasMore.value = notifications.value.length < total.value
  } catch (err: any) {
    ElMessage.error(err?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadConversations() {
  if (convLoading.value) return
  convLoading.value = true
  try {
    const res = await getConversations()
    conversations.value = res
  } catch (err: any) {
    ElMessage.error(err?.message || '加载失败')
  } finally {
    convLoading.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  pageNum.value++
  loadNotifications()
}

async function handleRead(item: NotificationVO) {
  if (item.isRead || !item.id) return
  try {
    await readNotifications([item.id])
    item.isRead = true
  } catch {
    // ignore
  }
}

async function handleReadAll() {
  try {
    const category = activeTab.value
    if (category === 'private') return
    await readAllNotifications(category)
    notifications.value.forEach(n => n.isRead = true)
    ElMessage.success('全部已读')
  } catch {
    ElMessage.error('操作失败')
  }
}

function goToPrivateMessage(conv: ConversationVO) {
  if (conv.conversationKey) {
    router.push(`/private-messages/${conv.conversationKey}`)
  }
}

function formatTime(time?: string): string {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

function getTypeLabel(type?: string): string {
  const map: Record<string, string> = {
    mention: '@我的',
    reply: '回复',
    comment: '评论',
    follow: '关注',
    collect: '收藏',
    like: '点赞',
    system: '系统'
  }
  return map[type || ''] || type || ''
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="notification-page">
    <div class="notification-container">
      <!-- 返回栏 -->
      <div class="back-bar">
        <button class="back-btn" @click="router.back()">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </button>
      </div>
      <!-- Tab 栏 -->
      <div class="tab-bar">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <el-icon class="tab-icon"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.label }}</span>
        </div>
        <el-button
          v-if="activeTab !== 'private'"
          class="read-all-btn"
          text
          :icon="Check"
          @click="handleReadAll"
        >
          全部已读
        </el-button>
      </div>

      <!-- 内容区域 -->
      <div class="content-area">
        <!-- 私信列表 -->
        <template v-if="activeTab === 'private'">
          <div v-if="convLoading && conversations.length === 0" class="loading-state">
            <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="conversations.length === 0" class="empty-state">
            <el-icon :size="48" class="empty-icon"><ChatLineRound /></el-icon>
            <p>暂无私信</p>
          </div>
          <div v-else class="conversation-list">
            <div
              v-for="conv in conversations"
              :key="conv.conversationKey"
              class="conversation-item"
              @click="goToPrivateMessage(conv)"
            >
              <el-avatar :size="48" :src="conv.otherUserAvatar" class="conv-avatar" />
              <div class="conv-info">
                <div class="conv-header">
                  <span class="conv-name">{{ conv.otherUserName }}</span>
                  <span class="conv-time">{{ formatTime(conv.lastMessageTime) }}</span>
                </div>
                <p class="conv-preview">{{ conv.lastMessage }}</p>
              </div>
              <el-badge
                v-if="conv.unreadCount && conv.unreadCount > 0"
                :value="conv.unreadCount"
                class="conv-unread"
              />
            </div>
          </div>
        </template>

        <!-- 通知列表 -->
        <template v-else>
          <div v-if="loading && notifications.length === 0" class="loading-state">
            <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
            <span>加载中...</span>
          </div>
          <div v-else-if="notifications.length === 0" class="empty-state">
            <el-icon :size="48" class="empty-icon"><NotificationIcon /></el-icon>
            <p>暂无通知</p>
          </div>
          <div v-else class="notification-list">
            <div
              v-for="item in notifications"
              :key="item.id"
              class="notification-item"
              :class="{ unread: !item.isRead }"
              @click="handleRead(item)"
            >
              <el-avatar
                :size="44"
                :src="item.senderAvatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'"
                class="notif-avatar"
              />
              <div class="notif-content">
                <div class="notif-header">
                  <span class="notif-sender">{{ item.senderName || '系统' }}</span>
                  <el-tag v-if="item.type" size="small" class="notif-type">
                    {{ getTypeLabel(item.type) }}
                  </el-tag>
                  <span class="notif-time">{{ formatTime(item.createTime) }}</span>
                </div>
                <p class="notif-title">{{ item.title }}</p>
                <p class="notif-text">{{ item.content }}</p>
              </div>
              <div v-if="!item.isRead" class="unread-dot" />
            </div>
            <div v-if="hasMore" class="load-more">
              <el-button text :loading="loading" @click="loadMore">加载更多</el-button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notification-page {
  min-height: 100vh;
  padding-top: 72px;
  background: linear-gradient(135deg, #0f1419 0%, #1e1b2e 100%);
}

.notification-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

/* 返回栏 */
.back-bar {
  margin-bottom: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  transform: translateX(-2px);
}

/* Tab 栏 */
.tab-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  padding: 6px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 12px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  justify-content: center;
}

.tab-item:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.05);
}

.tab-item.active {
  color: #e2e8f0;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%);
  box-shadow: 0 0 20px rgba(107, 70, 193, 0.15);
}

.tab-icon {
  font-size: 16px;
}

.read-all-btn {
  margin-left: auto;
  color: #94a3b8;
  font-size: 13px;
}

.read-all-btn:hover {
  color: #c4b5fd;
}

/* 内容区域 */
.content-area {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #64748b;
  gap: 12px;
}

.empty-icon {
  color: #475569;
  opacity: 0.5;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #64748b;
  gap: 12px;
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 会话列表 */
.conversation-list {
  display: flex;
  flex-direction: column;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.conversation-item:last-child {
  border-bottom: none;
}

.conversation-item:hover {
  background: rgba(107, 70, 193, 0.08);
}

.conv-avatar {
  flex-shrink: 0;
  border: 2px solid rgba(107, 70, 193, 0.3);
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.conv-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.conv-time {
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.conv-preview {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-unread :deep(.el-badge__content) {
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  border: none;
}

/* 通知列表 */
.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.25s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  position: relative;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: rgba(107, 70, 193, 0.08);
}

.notification-item.unread {
  background: rgba(107, 70, 193, 0.04);
}

.notification-item.unread:hover {
  background: rgba(107, 70, 193, 0.1);
}

.notif-avatar {
  flex-shrink: 0;
  border: 2px solid rgba(107, 70, 193, 0.3);
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.notif-sender {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.notif-type {
  font-size: 11px;
  height: 20px;
  line-height: 18px;
  padding: 0 6px;
  background: rgba(107, 70, 193, 0.2);
  border-color: rgba(107, 70, 193, 0.3);
  color: #c4b5fd;
}

.notif-time {
  font-size: 12px;
  color: #64748b;
  margin-left: auto;
  flex-shrink: 0;
}

.notif-title {
  font-size: 13px;
  font-weight: 500;
  color: #cbd5e1;
  margin: 0 0 2px;
}

.notif-text {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  flex-shrink: 0;
  margin-top: 6px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.load-more :deep(.el-button) {
  color: #94a3b8;
}

.load-more :deep(.el-button:hover) {
  color: #c4b5fd;
}
</style>
