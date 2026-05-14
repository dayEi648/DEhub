<template>
  <nav class="admin-nav">
    <div class="container nav-inner">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        {{ item.label }}
      </router-link>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/admin/users', label: '用户管理' }
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<style scoped>
.admin-nav {
  background: var(--text-white);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.nav-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 44px;
}
.nav-item {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 400;
  color: var(--text-secondary);
  text-decoration: none;
  padding: 4px 0;
  transition: color 0.2s;
  position: relative;
}
.nav-item:hover {
  color: var(--text-primary);
}
.nav-item.active {
  color: var(--text-primary);
  font-weight: 500;
}
.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--apple-blue);
  border-radius: 1px;
}
</style>
