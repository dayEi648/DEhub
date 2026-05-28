<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Loading, Promotion } from '@element-plus/icons-vue'
import { getMessages, sendMessage, readMessages } from '@/api/privateMessage'
import { getUserById } from '@/api/user'
import { getUser } from '@/utils/authStorage'
import type { PrivateMessageVO } from '@/types/privateMessage'
import type { UserVO } from '@/types/user'

const route = useRoute()
const router = useRouter()

const conversationKey = route.params.conversationKey as string

const messages = ref<PrivateMessageVO[]>([])
const pageNum = ref(1)
const pageSize = ref(20)
const total = ref(0)
const loading = ref(false)
const hasMore = ref(true)

const inputContent = ref('')
const sending = ref(false)

const currentUserId = ref<number | null>(null)

const otherUser = ref<UserVO | null>(null)

async function loadOtherUser() {
  const otherId = getOtherUserId(conversationKey)
  if (!otherId) return
  try {
    otherUser.value = await getUserById(otherId)
  } catch {
    // ignore
  }
}

async function loadMessages() {
  if (loading.value) return
  loading.value = true
  try {
    const res = await getMessages(conversationKey, pageNum.value, pageSize.value)
    if (pageNum.value === 1) {
      messages.value = res.records.reverse()
    } else {
      messages.value.unshift(...res.records.reverse())
    }
    total.value = res.total
    hasMore.value = messages.value.length < total.value
  } catch (err: any) {
    ElMessage.error(err?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function handleSend() {
  const content = inputContent.value.trim()
  if (!content || sending.value) return

  // 解析对方用户ID
  const otherId = getOtherUserId(conversationKey)
  if (!otherId) {
    ElMessage.error('无法确定接收者')
    return
  }

  sending.value = true
  try {
    await sendMessage({ receiverId: otherId, content })
    inputContent.value = ''
    // 从 authStorage 获取当前用户信息，构造本地消息追加
    const currentUser = getUser()
    messages.value.push({
      id: Date.now(),
      senderId: currentUserId.value ?? undefined,
      senderName: currentUser?.name || currentUser?.username,
      senderAvatar: currentUser?.avatar,
      receiverId: otherId,
      conversationKey,
      content,
      isRead: false,
      createTime: new Date().toISOString()
    })
    scrollToBottom()
  } catch (err: any) {
    ElMessage.error(err?.message || '发送失败')
  } finally {
    sending.value = false
  }
}

function loadMore() {
  if (loading.value || !hasMore.value) return
  pageNum.value++
  loadMessages()
}

function getOtherUserId(key: string): number | null {
  const parts = key.split(':')
  if (parts.length !== 2) return null
  const id1 = parseInt(parts[0] || '0')
  const id2 = parseInt(parts[1] || '0')
  if (currentUserId.value == null) return null
  return currentUserId.value === id1 ? id2 : id1
}

function isSelf(msg: PrivateMessageVO): boolean {
  return msg.senderId === currentUserId.value
}

function formatTime(time?: string): string {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function scrollToBottom() {
  setTimeout(() => {
    const container = document.querySelector('.msg-scroll-area')
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  }, 50)
}

function goBack() {
  router.back()
}

onMounted(() => {
  const user = getUser()
  currentUserId.value = user?.id || null
  loadOtherUser()
  loadMessages()
  readMessages(conversationKey).catch(() => {})
})
</script>

<template>
  <div class="pm-page">
    <div class="pm-container">
      <!-- 顶部栏 -->
      <div class="pm-header">
        <div class="pm-header-left">
          <el-button text :icon="ArrowLeft" class="back-btn" @click="goBack" />
          <span class="pm-title">{{ otherUser?.name || otherUser?.username || '私信对话' }}</span>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="msg-scroll-area">
        <div v-if="hasMore" class="load-more-area">
          <el-button text :loading="loading" size="small" @click="loadMore">加载更多</el-button>
        </div>

        <div v-if="loading && messages.length === 0" class="loading-state">
          <el-icon class="loading-icon" :size="32"><Loading /></el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="messages.length === 0" class="empty-state">
          <p>暂无消息，开始对话吧</p>
        </div>

        <div v-else class="msg-list">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="msg-item"
            :class="{ self: isSelf(msg) }"
          >
            <el-avatar
              :size="36"
              :src="msg.senderAvatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'"
              class="msg-avatar"
            />
            <div class="msg-bubble-wrap">
              <div class="msg-meta">
                <span class="msg-name">{{ msg.senderName || '用户' }}</span>
                <span class="msg-time">{{ formatTime(msg.createTime) }}</span>
              </div>
              <div class="msg-bubble">
                {{ msg.content }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="pm-input-area">
        <el-input
          v-model="inputContent"
          type="textarea"
          :rows="2"
          placeholder="输入消息..."
          resize="none"
          class="pm-input"
          @keydown.enter.prevent="handleSend"
        />
        <el-button
          type="primary"
          :icon="Promotion"
          :loading="sending"
          class="send-btn"
          @click="handleSend"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pm-page {
  min-height: 100vh;
  padding-top: 72px;
  background: linear-gradient(135deg, #0f1419 0%, #1e1b2e 100%);
  display: flex;
  flex-direction: column;
}

.pm-container {
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 72px);
}

/* 顶部栏 */
.pm-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px 16px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: none;
}

.pm-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-btn {
  color: #94a3b8;
  font-size: 16px;
}

.back-btn:hover {
  color: #e2e8f0;
}

.pm-title {
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
}

/* 消息滚动区域 */
.msg-scroll-area {
  flex: 1;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  padding: 16px;
}

.load-more-area {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
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

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #64748b;
}

/* 消息列表 */
.msg-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.msg-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.msg-item.self {
  flex-direction: row-reverse;
}

.msg-avatar {
  flex-shrink: 0;
  border: 2px solid rgba(107, 70, 193, 0.3);
}

.msg-bubble-wrap {
  display: flex;
  flex-direction: column;
  max-width: 70%;
}

.msg-item.self .msg-bubble-wrap {
  align-items: flex-end;
}

.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.msg-item.self .msg-meta {
  flex-direction: row-reverse;
}

.msg-name {
  font-size: 12px;
  color: #94a3b8;
}

.msg-time {
  font-size: 11px;
  color: #64748b;
}

.msg-bubble {
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.msg-item.self .msg-bubble {
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.5) 0%, rgba(236, 72, 153, 0.4) 100%);
  color: #fff;
}

/* 输入区域 */
.pm-input-area {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 0 0 16px 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-top: none;
}

.pm-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  border-radius: 12px;
}

.pm-input :deep(.el-textarea__inner:focus) {
  border-color: rgba(107, 70, 193, 0.5);
}

.pm-input :deep(.el-textarea__inner::placeholder) {
  color: #475569;
}

.send-btn {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border: none;
  border-radius: 12px;
  height: 44px;
  padding: 0 20px;
}

.send-btn:hover {
  opacity: 0.9;
}
</style>
