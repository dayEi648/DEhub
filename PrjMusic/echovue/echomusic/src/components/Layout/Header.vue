<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  ArrowDown,
  User,
  House,
  SwitchButton,
  ChatDotRound
} from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import { logout as logoutApi } from '@/api/user'
import { getUser, clearAuth } from '@/utils/authStorage'

defineProps<{
  title: string
  breadcrumb?: string[]
}>()

const router = useRouter()
const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')

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
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">{{ title }}</h1>
      <nav v-if="breadcrumb" class="breadcrumb">
        <span v-for="(item, index) in breadcrumb" :key="index" class="breadcrumb-item">
          {{ item }}
          <span v-if="index < breadcrumb.length - 1" class="breadcrumb-separator">/</span>
        </span>
      </nav>
    </div>

    <div class="header-right">
      <div class="search-box">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="全局搜索..."
          class="search-input"
          @keyup.enter="handleSearch"
        />
      </div>

      <div class="header-actions">
        <el-tooltip content="AI 助手" placement="bottom">
          <el-icon class="action-icon" @click="router.push('/ai-chat')"><ChatDotRound /></el-icon>
        </el-tooltip>
        <NotificationBell />

        <el-dropdown trigger="click" popper-class="admin-dropdown-popper">
          <div class="user-profile">
            <el-avatar
              :size="36"
              :src="avatarUrl"
              class="user-avatar"
            />
            <span class="user-name">{{ displayName }}</span>
            <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="admin-dropdown-menu">
              <div class="dropdown-header">
                <el-avatar :size="48" :src="avatarUrl" />
                <div class="dropdown-meta">
                  <div class="dropdown-name">{{ displayName }}</div>
                  <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                </div>
              </div>
              <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
              <el-dropdown-item :icon="ChatDotRound" @click="router.push('/ai-chat')">AI 助手</el-dropdown-item>
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
.header {
  height: 160px;
  background: rgba(26, 31, 46, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.breadcrumb {
  font-size: 13px;
  color: #64748b;
}

.breadcrumb-item {
  color: #94a3b8;
}

.breadcrumb-separator {
  margin: 0 8px;
  color: #475569;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.search-box {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: #64748b;
  font-size: 16px;
}

.search-input {
  width: 100%;
  height: 40px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 0 16px 0 40px;
  color: #e2e8f0;
  font-size: 14px;
  transition: all 0.3s ease;
}

.search-input::placeholder {
  color: #64748b;
}

.search-input:focus {
  outline: none;
  border-color: #6b46c1;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(107, 70, 193, 0.2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
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
  background: rgba(255, 255, 255, 0.1);
}

.notification-badge :deep(.el-badge__content) {
  background: linear-gradient(135deg, #ec4899 0%, #6b46c1 100%);
  border: none;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 24px;
  transition: all 0.3s ease;
}

.user-profile:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-avatar {
  border: 2px solid rgba(107, 70, 193, 0.5);
  box-shadow: 0 0 10px rgba(107, 70, 193, 0.3);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
}

.dropdown-icon {
  color: #64748b;
  font-size: 12px;
}
</style>

<style>
/* Dropdown popper styles (global) */
.admin-dropdown-popper {
  --el-dropdown-menuItem-hover-fill: rgba(107, 70, 193, 0.15);
  --el-dropdown-menuItem-hover-color: #e2e8f0;
}

.admin-dropdown-menu {
  background: linear-gradient(135deg, #1a1f2e 0%, #2d1b4e 100%) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.admin-dropdown-menu .dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.admin-dropdown-menu .dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-dropdown-menu .dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.admin-dropdown-menu .dropdown-level {
  font-size: 12px;
  color: #ec4899;
  font-weight: 500;
}

.admin-dropdown-menu .el-dropdown-menu__item {
  color: #94a3b8;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.admin-dropdown-menu .el-dropdown-menu__item:hover {
  color: #e2e8f0;
  background: rgba(107, 70, 193, 0.15);
}

.admin-dropdown-menu .el-dropdown-menu__item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>
