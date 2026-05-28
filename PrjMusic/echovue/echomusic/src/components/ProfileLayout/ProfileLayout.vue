<script setup lang="ts">
import { computed } from 'vue'
import {
  Star,
  Lock,
  Medal,
  User,
  Document,
  Tools,
  Brush,
  Connection
} from '@element-plus/icons-vue'
import { getUser } from '@/utils/authStorage'
import ProfileHeader from './ProfileHeader.vue'

export type ProfileTab =
  | 'favorites'
  | 'security'
  | 'vip'
  | 'space'
  | 'settings'
  | 'creator'
  | 'social'

const props = defineProps<{
  activeTab: ProfileTab
}>()

const emit = defineEmits<{
  (e: 'update:activeTab', val: ProfileTab): void
}>()

const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')

const navItems: { key: ProfileTab; label: string; icon: any }[] = [
  { key: 'favorites', label: '我的收藏', icon: Star },
  { key: 'social', label: '我的社交', icon: Connection },
  { key: 'security', label: '账号安全', icon: Lock },
  { key: 'vip', label: 'VIP权益', icon: Medal },
  { key: 'space', label: '个人空间', icon: User },
  { key: 'settings', label: '个人设置', icon: Tools },
  { key: 'creator', label: '创作者中心', icon: Brush }
]

function onNavClick(key: ProfileTab) {
  emit('update:activeTab', key)
}
</script>

<template>
  <div class="profile-layout">
    <ProfileHeader />

    <div class="profile-body">
      <!-- 左侧导航栏 -->
      <aside class="profile-sidebar">
        <div class="sidebar-user">
          <el-avatar :size="64" :src="avatarUrl" class="sidebar-avatar" />
          <div class="sidebar-name">{{ displayName }}</div>
          <div class="sidebar-level">Lv.{{ user?.level || 1 }}</div>
        </div>

        <nav class="profile-nav">
          <div
            v-for="item in navItems"
            :key="item.key"
            class="nav-item"
            :class="{ active: props.activeTab === item.key }"
            @click="onNavClick(item.key)"
          >
            <div class="nav-indicator" />
            <el-icon class="nav-icon"><component :is="item.icon" /></el-icon>
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.key !== 'favorites' && item.key !== 'settings' && item.key !== 'social' && item.key !== 'space'" class="nav-badge">即将上线</span>
          </div>
        </nav>
      </aside>

      <!-- 右侧内容区 -->
      <main class="profile-main">
        <div class="profile-content">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
@import './profile-layout.css';
</style>
