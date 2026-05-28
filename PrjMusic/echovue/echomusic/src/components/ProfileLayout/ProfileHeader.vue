<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  ArrowDown,
  User,
  House,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import { logout as logoutApi } from '@/api/user'
import { getUser, clearAuth } from '@/utils/authStorage'

const router = useRouter()
const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (user.value?.role ?? 0) >= 2)

const searchKeyword = ref('')

function handleSearch() {
  const kw = searchKeyword.value.trim()
  if (!kw) {
    ElMessage.info('请输入搜索关键词')
    return
  }
  router.push({ path: '/search', query: { keyword: kw, type: 'all' } })
}

function goHome() {
  router.push('/home')
}

function goProfile() {
  router.push('/profile')
}

function goAdmin() {
  router.push('/users')
}

async function handleLogout() {
  try {
    await logoutApi()
  } catch {
    /* 网络失败仍清除本地登录态 */
  }
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <header class="profile-header">
    <div class="header-inner">
      <!-- Logo -->
      <div class="brand" @click="goHome">
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

      <!-- 搜索 -->
      <div class="search-wrap">
        <div class="search-box">
          <el-icon class="search-icon"><Search /></el-icon>
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="搜索音乐、歌单、歌手..."
            class="search-input"
            @keyup.enter="handleSearch"
          />
        </div>
      </div>

      <!-- 右侧用户区 -->
      <div class="header-actions">
        <NotificationBell />

        <el-dropdown trigger="click" popper-class="profile-dropdown-popper">
          <div class="user-card">
            <el-avatar :size="36" :src="avatarUrl" class="user-avatar" />
            <div class="user-info">
              <span class="user-name">{{ displayName }}</span>
              <span class="user-level">Lv.{{ user?.level || 1 }}</span>
            </div>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="profile-dropdown-menu">
              <div class="dropdown-header">
                <el-avatar :size="48" :src="avatarUrl" />
                <div class="dropdown-meta">
                  <div class="dropdown-name">{{ displayName }}</div>
                  <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                </div>
              </div>
              <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
              <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goAdmin">管理后台</el-dropdown-item>
              <el-dropdown-item :icon="House" @click="goHome">返回首页</el-dropdown-item>
              <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>

<style scoped>
.profile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 72px;
  background: rgba(10, 6, 20, 0.65);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(107, 70, 193, 0.1);
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
  cursor: pointer;
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
  background: linear-gradient(90deg, #e2e8f0 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.brand-slogan {
  font-size: 11px;
  color: #64748b;
  letter-spacing: 1px;
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
  box-shadow: 0 0 0 3px rgba(107, 70, 193, 0.15), 0 4px 20px rgba(107, 70, 193, 0.1);
}

/* Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.notify-badge :deep(.el-badge__content) {
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
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
  color: #a78bfa;
  font-weight: 600;
}

.dropdown-arrow {
  color: #64748b;
  font-size: 12px;
  margin-left: 2px;
}
</style>

<style>
/* Dropdown popper styles (global) */
.profile-dropdown-popper {
  --el-dropdown-menuItem-hover-fill: rgba(107, 70, 193, 0.15);
  --el-dropdown-menuItem-hover-color: #e2e8f0;
}

.profile-dropdown-menu {
  background: linear-gradient(135deg, #1a1025 0%, #2d1b4e 100%) !important;
  border: 1px solid rgba(107, 70, 193, 0.15) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.profile-dropdown-menu .dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.profile-dropdown-menu .dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.profile-dropdown-menu .dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.profile-dropdown-menu .dropdown-level {
  font-size: 12px;
  color: #ec4899;
  font-weight: 500;
}

.profile-dropdown-menu .el-dropdown-menu__item {
  color: #94a3b8;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.profile-dropdown-menu .el-dropdown-menu__item:hover {
  color: #e2e8f0;
  background: rgba(107, 70, 193, 0.15);
}

.profile-dropdown-menu .el-dropdown-menu__item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>
