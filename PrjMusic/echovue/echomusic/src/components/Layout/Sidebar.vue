<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  User,
  Headset,
  Setting,
  DataLine,
  Back,
  Collection,
  Picture
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

const menuItems = [
  { index: '/home', title: '返回首页', icon: Back },
  { index: '/users', title: '用户管理', icon: User },
  { index: '/music', title: '音乐管理', icon: Headset },
  { index: '/albums', title: '专辑管理', icon: Collection },
  { index: '/banners', title: '推送管理', icon: Picture },
  { index: '/statistics', title: '数据统计', icon: DataLine },
  { index: '/settings', title: '系统设置', icon: Setting }
]
</script>

<template>
  <aside class="sidebar">
    <div class="logo" @click="router.push('/home')">
      <div class="logo-icon">
        <el-icon size="28"><Headset /></el-icon>
      </div>
      <span class="logo-text">回声记忆</span>
    </div>

    <nav class="menu">
      <div
        v-for="item in menuItems"
        :key="item.index"
        :class="['menu-item', { active: activeMenu === item.index }]"
        @click="router.push(item.index)"
      >
        <el-icon size="18"><component :is="item.icon" /></el-icon>
        <span class="menu-title">{{ item.title }}</span>
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="playing-indicator">
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
      </div>
      <span class="footer-text">Echo Memory</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 220px;
  height: 100vh;
  background: linear-gradient(180deg, #1a1f2e 0%, #2d1b4e 100%);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.logo {
  height: 70px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.logo:hover {
  opacity: 0.85;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-right: 12px;
  box-shadow: 0 4px 15px rgba(107, 70, 193, 0.4);
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(90deg, #e2e8f0 0%, #ec4899 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.menu {
  flex: 1;
  padding: 20px 12px;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  margin-bottom: 8px;
  border-radius: 12px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

.menu-item.active {
  background: linear-gradient(90deg, rgba(107, 70, 193, 0.3) 0%, rgba(236, 72, 153, 0.2) 100%);
  color: #e2e8f0;
  box-shadow: 0 0 20px rgba(107, 70, 193, 0.3);
  border: 1px solid rgba(236, 72, 153, 0.3);
}

.menu-title {
  margin-left: 12px;
  font-size: 15px;
  font-weight: 500;
}

.sidebar-footer {
  height: 60px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 20px;
}

.playing-indicator {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 20px;
}

.wave-bar {
  width: 3px;
  background: linear-gradient(180deg, #6b46c1 0%, #ec4899 100%);
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
}

.wave-bar:nth-child(1) { height: 8px; animation-delay: 0s; }
.wave-bar:nth-child(2) { height: 16px; animation-delay: 0.1s; }
.wave-bar:nth-child(3) { height: 12px; animation-delay: 0.2s; }
.wave-bar:nth-child(4) { height: 18px; animation-delay: 0.3s; }

@keyframes wave {
  0%, 100% { transform: scaleY(0.5); opacity: 0.7; }
  50% { transform: scaleY(1); opacity: 1; }
}

.footer-text {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}
</style>
