<script setup lang="ts">
import { Search, House, Star, User, Setting, SwitchButton, ArrowDown, ChatDotRound, ChatLineRound, Message, Notification as NotificationIcon, Compass, ChatRound } from '@element-plus/icons-vue'
import { getUser, getToken } from '@/utils/authStorage'
import { getUnreadCount } from '@/api/notification'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { NotificationUnreadCount } from '@/types/notification'

const props = defineProps<{
  searchKeyword: string
}>()

const emit = defineEmits<{
  (e: 'update:searchKeyword', val: string): void
  (e: 'search'): void
  (e: 'goAdmin'): void
  (e: 'goProfile'): void
  (e: 'logout'): void
}>()

const router = useRouter()
const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (user.value?.role ?? 0) >= 2)

const navItems = [
  { label: '发现音乐', icon: Compass, path: '/discover', active: false },
  { label: 'AI 助手', icon: ChatRound, path: '/ai-chat', active: false },
  { label: '我的收藏', icon: Star, path: '/profile', active: false }
]

function onNavClick(item: typeof navItems[0]) {
  if (item.path) {
    router.push(item.path)
  }
}

function onSearch() {
  emit('search')
}

// ========== 通知中心 ==========
const unreadCount = ref<NotificationUnreadCount>({
  total: 0,
  mention: 0,
  reply: 0,
  notify: 0,
  privateMessage: 0
})

async function fetchUnreadCount() {
  if (!getToken()) return
  try {
    const data = await getUnreadCount()
    unreadCount.value = data
  } catch {
    // 静默失败，不影响用户体验
  }
}

const notifyCategories = [
  { key: 'mention', label: '@我的', icon: ChatDotRound, countKey: 'mention' as const, tab: 'mention' },
  { key: 'privateMessage', label: '私信', icon: ChatLineRound, countKey: 'privateMessage' as const, tab: 'private' },
  { key: 'reply', label: '评论', icon: Message, countKey: 'reply' as const, tab: 'comment' },
  { key: 'notify', label: '通知', icon: NotificationIcon, countKey: 'notify' as const, tab: 'notify' }
]

function goToNotifications(tab: string) {
  router.push(`/notifications?tab=${tab}`)
}

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (!getToken()) return
  fetchUnreadCount()
  timer = setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <header class="home-header">
    <div class="header-inner">
      <!-- Logo -->
      <div class="brand">
        <div class="brand-logo">
          <div class="logo-icon">
            <div class="sound-wave">
              <span v-for="i in 4" :key="i" class="wave-bar" />
            </div>
          </div>
          <div class="brand-text">
            <span class="brand-name">EchoMemory</span>
            <span class="brand-slogan">回声记忆</span>
          </div>
        </div>
      </div>

      <!-- 导航 -->
      <nav class="main-nav">
        <a
          v-for="item in navItems"
          :key="item.label"
          href="javascript:;"
          class="nav-link"
          :class="{ active: item.active }"
          @click="onNavClick(item)"
        >
          <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </a>
      </nav>

      <!-- 搜索 -->
      <div class="search-wrap">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            :value="searchKeyword"
            type="text"
            placeholder="搜索音乐、歌单、歌手..."
            class="search-input"
            @input="$emit('update:searchKeyword', ($event.target as HTMLInputElement).value)"
            @keyup.enter="onSearch"
          />
        </div>
      </div>

      <!-- 右侧用户区 -->
      <div class="header-actions">
        <el-popover trigger="hover" :show-arrow="false" popper-class="notify-popover" :offset="8">
          <template #default>
            <div class="notify-panel">
              <div
                v-for="cat in notifyCategories"
                :key="cat.key"
                class="notify-category"
                @click="goToNotifications(cat.tab)"
              >
                <div class="notify-cat-left">
                  <el-icon class="notify-cat-icon"><component :is="cat.icon" /></el-icon>
                  <span class="notify-cat-label">{{ cat.label }}</span>
                </div>
                <el-badge
                  v-if="unreadCount[cat.countKey] > 0"
                  :value="unreadCount[cat.countKey]"
                  class="notify-cat-badge"
                />
              </div>
            </div>
          </template>
          <template #reference>
            <el-badge :value="unreadCount.total" :hidden="unreadCount.total === 0" class="notify-badge">
              <el-icon size="28" class="action-icon"><Message /></el-icon>
            </el-badge>
          </template>
        </el-popover>

        <el-dropdown trigger="click" popper-class="user-dropdown-popper">
          <div class="user-card">
            <el-avatar :size="36" :src="avatarUrl" class="user-avatar" />
            <div class="user-info">
              <span class="user-name">{{ displayName }}</span>
              <span class="user-level">Lv.{{ user?.level || 1 }}</span>
            </div>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="user-dropdown-menu">
              <div class="dropdown-header">
                <el-avatar :size="48" :src="avatarUrl" />
                <div class="dropdown-meta">
                  <div class="dropdown-name">{{ displayName }}</div>
                  <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                </div>
              </div>
              <el-dropdown-item :icon="User" @click="$emit('goProfile')">个人中心</el-dropdown-item>
              <el-dropdown-item :icon="ChatRound" @click="router.push('/ai-chat')">AI 助手</el-dropdown-item>
              <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="$emit('goAdmin')">管理后台</el-dropdown-item>
              <el-dropdown-item divided :icon="SwitchButton" @click="$emit('logout')">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<style scoped>
.home-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 72px;
  background: rgba(15, 20, 25, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

/* 底部微光边框 */
.home-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, #6b46c1 20%, #ec4899 50%, #06b6d4 80%, transparent 100%);
  background-size: 200% 100%;
  animation: shimmer 4s linear infinite;
  opacity: 0.6;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  gap: 24px;
}

/* Brand */
.brand {
  flex-shrink: 0;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 15px rgba(107, 70, 193, 0.4);
}

.sound-wave {
  display: flex;
  align-items: center;
  gap: 2px;
  height: 18px;
}

.wave-bar {
  width: 3px;
  background: white;
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
}

.wave-bar:nth-child(1) { height: 8px; animation-delay: 0s; }
.wave-bar:nth-child(2) { height: 14px; animation-delay: 0.15s; }
.wave-bar:nth-child(3) { height: 10px; animation-delay: 0.3s; }
.wave-bar:nth-child(4) { height: 16px; animation-delay: 0.45s; }

@keyframes wave {
  0%, 100% { transform: scaleY(0.6); opacity: 0.7; }
  50% { transform: scaleY(1); opacity: 1; }
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.brand-name {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-slogan {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 1px;
}

/* Nav */
.main-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 10px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.3s ease;
}

.nav-link {
  position: relative;
  overflow: hidden;
}

.nav-link:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.05);
}

/* hover 时下划线动画 */
.nav-link::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #6b46c1, #ec4899);
  border-radius: 1px;
  transition: all 0.3s ease;
  transform: translateX(-50%);
}

.nav-link:hover::after {
  width: 60%;
}

.nav-link.active {
  color: #e2e8f0;
  background: linear-gradient(135deg, rgba(107, 70, 193, 0.25) 0%, rgba(236, 72, 153, 0.15) 100%);
  box-shadow: 0 0 20px rgba(107, 70, 193, 0.15);
}

.nav-link.active::after {
  width: 60%;
}

.nav-icon {
  font-size: 16px;
}

/* Search */
.search-wrap {
  flex: 1;
  max-width: 420px;
  min-width: 200px;
}

.search-box {
  position: relative;
  width: 100%;
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 16px;
  z-index: 1;
}

.search-input {
  width: 100%;
  height: 42px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 21px;
  padding: 0 16px 0 42px;
  color: #e2e8f0;
  font-size: 14px;
  transition: all 0.3s ease;
  outline: none;
}

.search-input::placeholder {
  color: #475569;
}

.search-input:focus {
  border-color: rgba(107, 70, 193, 0.5);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(107, 70, 193, 0.15), 0 0 30px rgba(107, 70, 193, 0.2);
}

/* Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.notify-badge {
  display: inline-flex;
  position: relative;
  overflow: visible;
}

.notify-badge :deep(.el-badge__content) {
  right: 2px;
  top: 2px;
  transform: none;
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  border: none;
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 5px;
}

.action-icon {
  color: #94a3b8;
  cursor: pointer;
  padding: 8px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.action-icon:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.08);
}

/* User Card */
.user-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px 6px 6px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(107, 70, 193, 0.3);
  box-shadow: 0 4px 20px rgba(107, 70, 193, 0.1);
}

.user-avatar {
  border: 2px solid rgba(107, 70, 193, 0.4);
  box-shadow: 0 0 10px rgba(107, 70, 193, 0.2);
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
}

.user-level {
  font-size: 11px;
  color: #ec4899;
  font-weight: 600;
}

.dropdown-arrow {
  color: #64748b;
  font-size: 12px;
  margin-left: 2px;
}

/* Notify panel styles */
.notify-panel {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 120px;
}

.notify-category {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  color: #cbd5e1;
  font-size: 14px;
}

.notify-category:hover {
  background: rgba(107, 70, 193, 0.15);
  color: #e2e8f0;
}

.notify-cat-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.notify-cat-icon {
  font-size: 16px;
  color: #94a3b8;
}

.notify-category:hover .notify-cat-icon {
  color: #c4b5fd;
}

.notify-cat-badge {
  display: inline-flex;
  position: relative;
  overflow: visible;
}

.notify-cat-badge :deep(.el-badge__content) {
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  border: none;
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 5px;
}
</style>

<style>
/* Dropdown popper styles (global) */
.user-dropdown-popper {
  --el-dropdown-menuItem-hover-fill: rgba(107, 70, 193, 0.15);
  --el-dropdown-menuItem-hover-color: #e2e8f0;
}

.user-dropdown-menu {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.user-dropdown-menu .dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.user-dropdown-menu .dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-dropdown-menu .dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.user-dropdown-menu .dropdown-level {
  font-size: 12px;
  color: #ec4899;
  font-weight: 500;
}

.user-dropdown-menu .el-dropdown-menu__item {
  color: #94a3b8;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.user-dropdown-menu .el-dropdown-menu__item:hover {
  color: #e2e8f0;
  background: rgba(107, 70, 193, 0.15);
}

.user-dropdown-menu .el-dropdown-menu__item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}

/* Notify popover override */
.notify-popover {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  overflow: visible !important;
}

.notify-popover .el-popover__title {
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  padding: 4px 6px;
}
</style>
