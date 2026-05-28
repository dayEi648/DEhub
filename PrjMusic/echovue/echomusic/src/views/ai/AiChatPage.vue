<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatRound,
  Plus,
  Delete,
  ChatDotRound,
  ArrowLeft,
  ArrowRight,
  Microphone,
  Stopwatch,
  Loading,
  Promotion
} from '@element-plus/icons-vue'
import {
  chatStream,
  getSessions,
  getMessages,
  deleteSession,
  heartbeat,
  clearMemory
} from '@/api/aiAgent'
import { getUser } from '@/utils/authStorage'
import type { AiSession, AiMessage, SseCallbacks, ToolResult, MusicItem } from '@/types/aiAgent'

const router = useRouter()
const user = computed(() => getUser())

// ==================== 会话管理 ====================
const sessions = ref<AiSession[]>([])
const currentSessionId = ref<string>('')
const sessionLoading = ref(false)

// ==================== 消息列表 ====================
interface MusicCard {
  id: number
  name: string
  coverUrl: string
  vip: boolean
}

interface DisplayMessage {
  role: 'user' | 'assistant' | 'tool' | 'cards'
  content: string
  cards?: MusicCard[]
  isStreaming?: boolean
}

const messages = ref<DisplayMessage[]>([])
const isStreaming = ref(false)
const inputMessage = ref('')
const textareaRef = ref<HTMLTextAreaElement>()
const messagesEndRef = ref<HTMLDivElement>()

// 心跳定时器
let heartbeatTimer: ReturnType<typeof setInterval> | null = null

// ==================== 初始化 ====================

onMounted(() => {
  loadSessions()
  const autoMsg = (history.state as any)?.autoMessage
  if (autoMsg) {
    inputMessage.value = autoMsg
    window.history.replaceState({}, '', location.href)
    nextTick(() => handleSend())
  }
})

onBeforeUnmount(() => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  // 页面卸载时清理 Redis 内存缓存
  const sid = currentSessionId.value
  if (sid && typeof navigator !== 'undefined' && navigator.sendBeacon) {
    navigator.sendBeacon(`/api/ai/sessions/${sid}/memory`)
  }
})

// ==================== 会话操作 ====================

async function loadSessions() {
  sessionLoading.value = true
  try {
    sessions.value = await getSessions()
  } catch {
    /* 错误已由拦截器提示 */
  } finally {
    sessionLoading.value = false
  }
}

async function selectSession(sessionId: string) {
  if (currentSessionId.value === sessionId) return
  currentSessionId.value = sessionId
  messages.value = []
  await loadMessages(sessionId)
  startHeartbeat(sessionId)
}

async function loadMessages(sessionId: string) {
  try {
    const list = await getMessages(sessionId, 1, 100)
    messages.value = list.map((m: AiMessage) => ({
      role: m.role,
      content: m.content
    }))
    scrollToBottom()
  } catch {
    /* ignore */
  }
}

function startHeartbeat(sessionId: string) {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
  }
  heartbeatTimer = setInterval(() => {
    heartbeat(sessionId).catch(() => {
      /* 心跳失败不提示 */
    })
  }, 30000)
}

function createNewSession() {
  currentSessionId.value = ''
  messages.value = []
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  nextTick(() => textareaRef.value?.focus())
}

async function handleDeleteSession(sessionId: string, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm('确定删除该会话吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteSession(sessionId)
    ElMessage.success('删除成功')
    if (currentSessionId.value === sessionId) {
      createNewSession()
    }
    await loadSessions()
  } catch (e: any) {
    if (e !== 'cancel') {
      /* 删除失败已由拦截器提示 */
    }
  }
}

// ==================== 对话发送 ====================

async function handleSend() {
  const text = inputMessage.value.trim()
  if (!text || isStreaming.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: text })
  inputMessage.value = ''
  adjustTextareaHeight()
  scrollToBottom()

  // 添加空的 AI 消息占位
  const assistantIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', isStreaming: true })
  isStreaming.value = true

  const callbacks: SseCallbacks = {
    onMessageDelta: (delta: string) => {
      const msg = messages.value[assistantIndex]
      if (msg) {
        msg.content += delta
        scrollToBottom()
      }
    },
    onToolEnd: (data: any) => {
      const tools: ToolResult[] = data.tool_results || []
      for (const tool of tools) {
        // 提取音乐卡片
        const cards = extractMusicCards(tool)
        if (cards.length > 0) {
          messages.value.push({
            role: 'cards',
            content: '',
            cards
          })
        }
        // 同时插入文本提示（简化版）
        const hint = formatToolResult(tool)
        if (hint) {
          messages.value.push({
            role: 'tool',
            content: hint
          })
        }
      }
      scrollToBottom()
    },
    onDone: (data: { session_id: string; intent: string }) => {
      isStreaming.value = false
      const msg = messages.value[assistantIndex]
      if (msg) {
        msg.isStreaming = false
      }
      // 如果是新会话，更新 sessionId 并刷新列表
      if (!currentSessionId.value && data.session_id) {
        currentSessionId.value = data.session_id
        startHeartbeat(data.session_id)
        loadSessions()
      }
      scrollToBottom()
    },
    onError: (msg: string) => {
      isStreaming.value = false
      const assistantMsg = messages.value[assistantIndex]
      if (assistantMsg) {
        assistantMsg.isStreaming = false
        if (!assistantMsg.content) {
          assistantMsg.content = '抱歉，发生了错误：' + msg
        }
      }
      scrollToBottom()
    }
  }

  await chatStream(
    { message: text, session_id: currentSessionId.value || undefined },
    callbacks
  )
}

function extractMusicCards(tool: ToolResult): MusicCard[] {
  const items: MusicItem[] =
    tool.recommendations ||
    tool.results ||
    (tool.data ? [tool.data] : [])

  return items.map((m) => ({
    id: m.id,
    name: m.name,
    coverUrl: m.cover_url || '',
    vip: !!m.vip
  }))
}

function formatToolResult(tool: ToolResult): string {
  const nameMap: Record<string, string> = {
    search_music: '搜索音乐',
    emotion_recommend: '个性推荐',
    interest_recommend: '个性推荐',
    add_to_playlist: '添加到歌单',
    play_music: '播放音乐',
    search_web: '联网搜索'
  }
  const name = nameMap[tool.tool] || tool.tool

  if (tool.status === 'ok' || tool.status === 'fallback_hot') {
    const count =
      (tool.recommendations?.length) ||
      (tool.results?.length) ||
      (tool.data ? 1 : 0)
    if (count > 0) {
      return `${name}：为您找到 ${count} 首相关歌曲`
    }
    return name
  }
  if (tool.status === 'auth_error') {
    return `${name}：登录已过期，请重新登录`
  }
  if (tool.status === 'error' && tool.message) {
    return `${name}：${tool.message}`
  }
  if (tool.message) {
    return `${name}：${tool.message}`
  }
  return name
}

function goToMusicDetail(id: number) {
  router.push(`/music/${id}`)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function adjustTextareaHeight() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

function goBack() {
  router.push('/home')
}

function handleMessageClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const link = target.closest('a.internal-link') as HTMLAnchorElement | null
  if (link) {
    event.preventDefault()
    const href = link.getAttribute('href')
    if (href) {
      router.push(href)
    }
  }
}

// ==================== Markdown 轻量渲染 ====================
function renderMarkdown(text: string): string {
  if (!text) return ''
  // 先转义 HTML 特殊字符（防止任意 HTML 注入）
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 代码块 ```...```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  // 行内代码 `...`
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  // 粗体 **...**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  // 斜体 *...*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  // 链接 [text](url) — 站内链接使用 internal-link，由 Vue Router 导航
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
    if (url.startsWith('/')) {
      return `<a href="${url}" class="internal-link">${text}</a>`
    }
    return `<a href="${url}" target="_blank" rel="noopener">${text}</a>`
  })

  return html
}

// ==================== 侧边栏折叠 ====================
const sidebarCollapsed = ref(false)
function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="ai-chat-page">
    <!-- 左侧会话列表 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo" @click="goBack">
          <el-icon size="22"><ArrowLeft /></el-icon>
          <span v-show="!sidebarCollapsed" class="logo-text">返回首页</span>
        </div>
        <el-button
          v-show="!sidebarCollapsed"
          type="primary"
          size="small"
          :icon="Plus"
          class="new-chat-btn"
          @click="createNewSession"
        >
          新对话
        </el-button>
      </div>

      <div v-show="!sidebarCollapsed" class="session-list">
        <div
          v-for="s in sessions"
          :key="s.session_id"
          :class="['session-item', { active: currentSessionId === s.session_id }]"
          @click="selectSession(s.session_id)"
        >
          <el-icon size="16"><ChatRound /></el-icon>
          <span class="session-title">{{ s.title || '新对话' }}</span>
          <el-icon
            size="14"
            class="delete-icon"
            @click="handleDeleteSession(s.session_id, $event)"
          >
            <Delete />
          </el-icon>
        </div>
        <div v-if="sessions.length === 0 && !sessionLoading" class="session-empty">
          暂无历史会话
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="user-mini" v-show="!sidebarCollapsed">
          <el-avatar :size="28" :src="user?.avatar" />
          <span class="user-name">{{ user?.name || user?.username || '用户' }}</span>
        </div>
      </div>

      <!-- 折叠按钮 -->
      <div class="collapse-btn" @click="toggleSidebar">
        <el-icon size="14">
          <component :is="sidebarCollapsed ? 'ArrowRight' : 'ArrowLeft'" />
        </el-icon>
      </div>
    </aside>

    <!-- 主聊天区域 -->
    <main class="chat-main">
      <!-- 顶部标题 -->
      <header class="chat-header">
        <div class="header-left">
          <el-icon size="20" class="chat-icon"><ChatDotRound /></el-icon>
          <h2 class="chat-title">AI 音乐助手</h2>
          <span v-if="isStreaming" class="streaming-badge">
            <el-icon class="spin-icon"><Stopwatch /></el-icon>
            思考中...
          </span>
        </div>
      </header>

      <!-- 消息列表 -->
      <div class="messages-container" @click="handleMessageClick">
        <!-- 欢迎语 -->
        <div v-if="messages.length === 0" class="welcome-area">
          <div class="welcome-card">
            <el-icon size="48" class="welcome-icon"><Microphone /></el-icon>
            <h3 class="welcome-title">回声记忆 AI 助手</h3>
            <p class="welcome-desc">
              基于情绪识别的个性化音乐平台智能助手。<br />
              你可以问我关于音乐推荐、歌单管理、歌曲搜索的问题。
            </p>
            <div class="quick-actions">
              <div class="quick-item" @click="inputMessage = '推荐一些适合放松的音乐';handleSend()">
                🎵 推荐一些适合放松的音乐
              </div>
              <div class="quick-item" @click="inputMessage = '根据我的听歌习惯推荐歌曲';handleSend()">
                🎧 根据我的听歌习惯推荐歌曲
              </div>
              <div class="quick-item" @click="inputMessage = '搜索周杰伦的歌曲';handleSend()">
                🔍 搜索周杰伦的歌曲
              </div>
            </div>
          </div>
        </div>

        <!-- 消息气泡 -->
        <template v-else>
          <div
            v-for="(msg, index) in messages"
            :key="index"
            :class="['message-row', msg.role]"
          >
            <!-- 用户头像 -->
            <el-avatar
              v-if="msg.role === 'user'"
              :size="36"
              :src="user?.avatar"
              class="msg-avatar"
            />
            <!-- AI 头像 -->
            <div v-else-if="msg.role === 'assistant'" class="ai-avatar">
              <el-icon size="20"><ChatRound /></el-icon>
            </div>

            <div :class="['message-bubble', msg.role]">
              <!-- 工具提示 -->
              <div v-if="msg.role === 'tool'" class="tool-hint">
                <el-icon size="12"><Stopwatch /></el-icon>
                <span>{{ msg.content }}</span>
              </div>
              <!-- 音乐推荐卡片 -->
              <div v-else-if="msg.role === 'cards' && msg.cards" class="music-cards">
                <div
                  v-for="card in msg.cards"
                  :key="card.id"
                  class="music-card"
                  @click="goToMusicDetail(card.id)"
                >
                  <div class="card-cover-wrap">
                    <img
                      :src="card.coverUrl || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'"
                      class="card-cover"
                      alt="cover"
                    />
                    <span v-if="card.vip" class="card-vip">VIP</span>
                  </div>
                  <div class="card-name">{{ card.name }}</div>
                </div>
              </div>
              <!-- 普通消息 -->
              <template v-else>
                <div v-if="msg.role === 'user'" class="message-text">{{ msg.content }}</div>
                <div v-else class="message-text" v-html="renderMarkdown(msg.content)"></div>
                <div v-if="msg.isStreaming" class="typing-cursor"></div>
              </template>
            </div>
          </div>
        </template>

        <div ref="messagesEndRef" />
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            ref="textareaRef"
            v-model="inputMessage"
            class="chat-textarea"
            placeholder="输入消息，按 Enter 发送，Shift+Enter 换行..."
            :disabled="isStreaming"
            rows="1"
            @keydown="handleKeydown"
            @input="adjustTextareaHeight"
          />
          <el-button
            type="primary"
            class="send-btn"
            :disabled="!inputMessage.trim() || isStreaming"
            @click="handleSend"
          >
            <el-icon size="18"><component :is="isStreaming ? 'Loading' : 'Promotion'" /></el-icon>
          </el-button>
        </div>
        <div class="input-hint">AI 生成内容仅供参考</div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.ai-chat-page {
  display: flex;
  height: 100vh;
  background: #0f1419;
  color: #e2e8f0;
  overflow: hidden;
}

/* ==================== 侧边栏 ==================== */
.sidebar {
  width: 260px;
  flex-shrink: 0;
  background: linear-gradient(180deg, #1a1f2e 0%, #2d1b4e 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  color: #94a3b8;
  transition: color 0.3s;
}

.logo:hover {
  color: #e2e8f0;
}

.logo-text {
  font-size: 14px;
  font-weight: 500;
}

.new-chat-btn {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border: none;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.3s ease;
  margin-bottom: 4px;
  position: relative;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

.session-item:hover .delete-icon {
  opacity: 1;
}

.session-item.active {
  background: linear-gradient(90deg, rgba(107, 70, 193, 0.25) 0%, rgba(236, 72, 153, 0.15) 100%);
  color: #e2e8f0;
  border: 1px solid rgba(236, 72, 153, 0.2);
}

.session-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-icon {
  opacity: 0;
  transition: opacity 0.2s;
  color: #64748b;
  padding: 2px;
  border-radius: 4px;
}

.delete-icon:hover {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.session-empty {
  text-align: center;
  color: #64748b;
  font-size: 12px;
  padding: 20px;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.user-mini {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-name {
  font-size: 13px;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collapse-btn {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background: #2d1b4e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
  z-index: 10;
}

.collapse-btn:hover {
  color: #e2e8f0;
  background: #3b2570;
}

/* ==================== 主区域 ==================== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 20, 25, 0.8);
  backdrop-filter: blur(10px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-icon {
  color: #6b46c1;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.streaming-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b46c1;
  background: rgba(107, 70, 193, 0.15);
  padding: 4px 10px;
  border-radius: 20px;
}

.spin-icon {
  animation: spin 1.5s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ==================== 消息区域 ==================== */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 欢迎区域 */
.welcome-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-card {
  text-align: center;
  max-width: 520px;
}

.welcome-icon {
  color: #6b46c1;
  margin-bottom: 16px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 12px;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-desc {
  color: #64748b;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.quick-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 14px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.quick-item:hover {
  background: rgba(107, 70, 193, 0.1);
  border-color: rgba(107, 70, 193, 0.3);
  color: #e2e8f0;
}

/* 消息气泡 */
.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  max-width: 85%;
}

.message-row.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-row.assistant {
  align-self: flex-start;
}

.message-row.tool {
  align-self: flex-start;
  padding-left: 48px;
}

.msg-avatar {
  border: 2px solid rgba(107, 70, 193, 0.3);
  flex-shrink: 0;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;
}

.message-bubble.user {
  background: linear-gradient(135deg, #6b46c1 0%, #8b5cf6 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  border-bottom-left-radius: 4px;
}

.message-bubble.tool {
  background: transparent;
  padding: 0;
}

.message-text {
  white-space: pre-wrap;
}

.tool-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  background: rgba(107, 70, 193, 0.08);
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid rgba(107, 70, 193, 0.15);
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 16px;
  background: #6b46c1;
  margin-left: 4px;
  animation: blink 1s step-end infinite;
  vertical-align: middle;
}

@keyframes blink {
  50% { opacity: 0; }
}

/* ==================== 输入区域 ==================== */
.input-area {
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(15, 20, 25, 0.9);
  backdrop-filter: blur(10px);
  padding-bottom: 80px; /* 为 PlayerBar 留出空间 */
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 10px 14px;
  transition: border-color 0.3s;
}

.input-wrapper:focus-within {
  border-color: rgba(107, 70, 193, 0.4);
  box-shadow: 0 0 0 3px rgba(107, 70, 193, 0.1);
}

.chat-textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  min-height: 24px;
  max-height: 120px;
  font-family: inherit;
}

.chat-textarea::placeholder {
  color: #64748b;
}

.chat-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border: none;
  flex-shrink: 0;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-hint {
  text-align: center;
  font-size: 11px;
  color: #475569;
  margin-top: 8px;
}

/* 滚动条 */
.messages-container::-webkit-scrollbar,
.session-list::-webkit-scrollbar {
  width: 4px;
}

.messages-container::-webkit-scrollbar-thumb,
.session-list::-webkit-scrollbar-thumb {
  background: rgba(107, 70, 193, 0.3);
  border-radius: 2px;
}

/* Markdown 样式 */
.code-block {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  color: #e2e8f0;
}

.code-block code {
  font-family: 'Courier New', monospace;
  background: transparent;
  padding: 0;
}

.inline-code {
  background: rgba(107, 70, 193, 0.15);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  color: #c4b5fd;
}

.message-text a {
  color: #8b5cf6;
  text-decoration: underline;
}

.message-text a:hover {
  color: #a78bfa;
}

/* 音乐推荐卡片 */
.music-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 4px 0;
}

.music-card {
  width: 140px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.music-card:hover {
  transform: translateY(-4px);
}

.card-cover-wrap {
  position: relative;
  width: 140px;
  height: 140px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.card-cover {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.music-card:hover .card-cover {
  transform: scale(1.05);
}

.card-vip {
  position: absolute;
  top: 6px;
  right: 6px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.card-name {
  margin-top: 8px;
  font-size: 13px;
  color: #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 100;
    height: 100%;
    transform: translateX(0);
  }
  .sidebar.collapsed {
    transform: translateX(-100%);
    width: 260px;
  }
  .message-row {
    max-width: 95%;
  }
}
</style>
