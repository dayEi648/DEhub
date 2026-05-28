<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChatDotRound,
  ChatLineRound,
  Message,
  Notification as NotificationIcon
} from '@element-plus/icons-vue'
import { getUnreadCount } from '@/api/notification'
import type { NotificationUnreadCount } from '@/types/notification'

const router = useRouter()

const unreadCount = ref<NotificationUnreadCount>({
  total: 0,
  mention: 0,
  reply: 0,
  notify: 0,
  privateMessage: 0
})

const notifyCategories = [
  { key: 'mention', label: '@我的', icon: ChatDotRound, countKey: 'mention' as const, tab: 'mention' },
  { key: 'privateMessage', label: '私信', icon: ChatLineRound, countKey: 'privateMessage' as const, tab: 'private' },
  { key: 'reply', label: '评论', icon: Message, countKey: 'reply' as const, tab: 'comment' },
  { key: 'notify', label: '通知', icon: NotificationIcon, countKey: 'notify' as const, tab: 'notify' }
]

async function fetchUnreadCount() {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data
  } catch {
    // 静默失败，不影响用户体验
  }
}

function goToNotifications(tab: string) {
  router.push(`/notifications?tab=${tab}`)
}

let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  fetchUnreadCount()
  timer = setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
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
</template>

<style scoped>
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
  padding: 6px;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.action-icon:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.08);
}

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
  padding: 10px 12px;
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
