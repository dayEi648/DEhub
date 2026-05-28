<script setup lang="ts">
import { Search, House, Star, User, Setting, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
import { getUser, clearAuth } from '@/utils/authStorage'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { logout as logoutApi } from '@/api/user'
import { ElMessage } from 'element-plus'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import { useDiscoverPage } from './useDiscoverPage'

// Sections
import OverviewSection from './sections/OverviewSection.vue'
import HotSongsSection from './sections/HotSongsSection.vue'
import NewSongsSection from './sections/NewSongsSection.vue'
import VipSection from './sections/VipSection.vue'
import PlaylistSection from './sections/PlaylistSection.vue'
import AlbumSection from './sections/AlbumSection.vue'
import EmotionBrowseSection from './sections/EmotionBrowseSection.vue'
import InterestBrowseSection from './sections/InterestBrowseSection.vue'
import StyleBrowseSection from './sections/StyleBrowseSection.vue'
import InstrumentBrowseSection from './sections/InstrumentBrowseSection.vue'
import LanguageBrowseSection from './sections/LanguageBrowseSection.vue'

const { activeTab, searchKeyword, tabList, switchTab, handleSearch, goToTab } = useDiscoverPage()

const router = useRouter()
const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (user.value?.role ?? 0) >= 2)

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
    /* ignore */
  }
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <div class="discover-page">
    <!-- 背景光晕 -->
    <div class="discover-bg-layers" aria-hidden="true" />

    <!-- 顶部栏 -->
    <div class="discover-header">
      <div class="header-main">
        <!-- 左侧品牌 -->
        <div class="header-left">
          <a class="brand-link" @click="goHome">
            <span class="brand-logo-mini">E</span>
            <span class="brand-text-mini">EchoMemory</span>
          </a>
        </div>

        <!-- 中间搜索 -->
        <div class="header-center">
          <div class="search-input-wrap">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索音乐、歌单、专辑、歌手..."
              class="search-input"
              size="large"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #append>
                <el-button type="primary" @click="handleSearch">搜索</el-button>
              </template>
            </el-input>
          </div>
        </div>

        <!-- 右侧用户 -->
        <div class="header-right">
          <NotificationBell />
          <el-dropdown trigger="click" popper-class="user-dropdown-popper">
            <div class="user-card-mini">
              <el-avatar :size="34" :src="avatarUrl" class="user-avatar-mini" />
              <span class="user-name-mini">{{ displayName }}</span>
              <el-icon class="dropdown-arrow-mini"><ArrowDown /></el-icon>
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
                <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
                <el-dropdown-item :icon="House" @click="goHome">返回首页</el-dropdown-item>
                <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goAdmin">管理后台</el-dropdown-item>
                <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- Tab 导航 -->
      <div class="discover-tabs">
        <div
          v-for="tab in tabList"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          {{ tab.label }}
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="discover-body">
      <OverviewSection v-if="activeTab === 'overview'" @go-tab="goToTab" />
      <HotSongsSection v-else-if="activeTab === 'hot'" />
      <NewSongsSection v-else-if="activeTab === 'new'" />
      <VipSection v-else-if="activeTab === 'vip'" />
      <PlaylistSection v-else-if="activeTab === 'playlist'" />
      <AlbumSection v-else-if="activeTab === 'album'" />
      <EmotionBrowseSection v-else-if="activeTab === 'emotion'" />
      <InterestBrowseSection v-else-if="activeTab === 'interest'" />
      <StyleBrowseSection v-else-if="activeTab === 'style'" />
      <InstrumentBrowseSection v-else-if="activeTab === 'instrument'" />
      <LanguageBrowseSection v-else-if="activeTab === 'language'" />
    </div>
  </div>
</template>

<style scoped src="./discover.css"></style>
