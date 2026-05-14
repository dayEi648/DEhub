<template>
  <nav class="global-nav">
    <div class="nav-inner container">
      <router-link to="/" class="nav-logo">DE hub</router-link>

      <div class="nav-links" :class="{ open: uiStore.isMobileMenuOpen }">
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: $route.path === link.to || $route.path.startsWith(link.to + '/') }"
          @click="uiStore.isMobileMenuOpen = false"
        >
          {{ link.label }}
        </router-link>
      </div>

      <div class="nav-right">
        <div class="user-menu" @click="toggleDropdown">
          <Avatar :src="authStore.user?.avatar_url" :name="authStore.user?.username || ''" :size="32" />
          <div v-if="dropdownOpen" class="dropdown">
            <router-link to="/profile" class="dropdown-item">个人中心</router-link>
            <div class="dropdown-divider" />
            <button class="dropdown-item" @click="handleLogout">登出</button>
          </div>
        </div>
        <button class="hamburger" @click="uiStore.toggleMobileMenu">
          ☰
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import Avatar from './Avatar.vue'

const authStore = useAuthStore()
const uiStore = useUiStore()
const dropdownOpen = ref(false)

const navLinks = [
  { to: '/blog', label: '博客' },
  { to: '/forum', label: '论坛' },
  { to: '/chat', label: 'AI 对话' },
  { to: '/links', label: '子网站' }
]

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function handleLogout() {
  dropdownOpen.value = false
  authStore.logout()
}
</script>

<style scoped>
.global-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  z-index: 1000;
}
.nav-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}
.nav-logo {
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 600;
  color: var(--text-white);
  letter-spacing: -0.224px;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}
.nav-link {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 400;
  color: var(--text-white);
  opacity: 0.8;
  transition: opacity 0.2s;
}
.nav-link:hover {
  opacity: 1;
}
.nav-link.active {
  opacity: 1;
  border-bottom: 1px solid var(--text-white);
  padding-bottom: 2px;
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user-menu {
  position: relative;
  cursor: pointer;
}
.dropdown {
  position: absolute;
  top: 44px;
  right: 0;
  background: var(--text-white);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  min-width: 140px;
  overflow: hidden;
}
.dropdown-item {
  display: block;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--text-primary);
  text-decoration: none;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
}
.dropdown-item:hover {
  background: var(--bg-gray);
}
.dropdown-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.06);
}
.hamburger {
  display: none;
  background: transparent;
  border: none;
  color: var(--text-white);
  font-size: 20px;
  cursor: pointer;
}

@media (max-width: 640px) {
  .nav-links {
    position: fixed;
    inset: 48px 0 0 0;
    background: rgba(0, 0, 0, 0.95);
    flex-direction: column;
    justify-content: center;
    gap: 32px;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  .nav-links.open {
    transform: translateX(0);
  }
  .nav-link {
    font-size: 21px;
    opacity: 1;
  }
  .hamburger {
    display: block;
  }
}
</style>
