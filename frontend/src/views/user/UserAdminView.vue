<template>
  <div class="user-admin-page">
    <div class="container">
      <template v-if="authStore.isAdmin">
        <h1 class="page-title">用户管理</h1>

        <div class="toolbar">
          <FilterButton
            as-input
            v-model="searchQuery"
            placeholder="搜索用户名/邮箱"
            @enter="handleSearch"
          />
          <select v-model="permissionFilter" class="filter-select">
            <option value="">全部权限</option>
            <option value="0">普通用户</option>
            <option value="1">管理员</option>
            <option value="2">超级管理员</option>
          </select>
          <label class="checkbox-label">
            <input v-model="includeDeleted" type="checkbox" />
            包含已注销
          </label>
          <PrimaryButton @click="handleSearch">查询</PrimaryButton>
        </div>

        <div v-if="userStore.userList.length" class="admin-table">
          <div class="table-row header">
            <div class="col-id">ID</div>
            <div class="col-user">用户</div>
            <div class="col-email">邮箱</div>
            <div class="col-perm">权限</div>
            <div class="col-date">注册时间</div>
            <div class="col-status">状态</div>
            <div class="col-actions">操作</div>
          </div>
          <div v-for="user in userStore.userList" :key="user.id" class="table-row">
            <div class="col-id">{{ user.id }}</div>
            <div class="col-user">
              <Avatar :src="user.avatar_url" :name="user.username" :size="32" />
              <span>{{ user.username }}</span>
            </div>
            <div class="col-email">{{ user.email }}</div>
            <div class="col-perm">
              <span class="perm-badge" :class="permClass(user.permission)">{{ permLabel(user.permission) }}</span>
            </div>
            <div class="col-date">{{ formatDate(user.created_at) }}</div>
            <div class="col-status">
              <span class="status-dot" :class="user.is_deleted ? 'deleted' : 'active'" />
              {{ user.is_deleted ? '已注销' : '正常' }}
            </div>
            <div class="col-actions">
              <button v-if="!user.is_deleted" class="action-link" @click="confirmDelete(user.id)">注销</button>
              <button class="action-link danger" @click="confirmHardDelete(user.id)">硬删除</button>
            </div>
          </div>
        </div>
        <EmptyState v-else description="暂无用户数据" />

        <Pagination
          v-if="userStore.totalUsers > pageSize"
          v-model:current-page="currentPage"
          :total="userStore.totalUsers"
          :page-size="pageSize"
        />
      </template>
      <EmptyState v-else description="权限不足，无法访问用户管理" />
    </div>

    <Modal v-model="deleteModalOpen" title="确认注销">
      <p>确定要注销该用户吗？注销后用户将变为不可用状态。</p>
      <template #footer>
        <button class="modal-btn" @click="deleteModalOpen = false">取消</button>
        <button class="modal-btn danger" @click="executeDelete">确认注销</button>
      </template>
    </Modal>

    <Modal v-model="hardDeleteModalOpen" title="确认硬删除">
      <p style="color: var(--error-red)">警告：此操作不可恢复，用户数据将从数据库彻底删除。</p>
      <template #footer>
        <button class="modal-btn" @click="hardDeleteModalOpen = false">取消</button>
        <button class="modal-btn danger" @click="executeHardDelete">确认删除</button>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useUiStore } from '@/stores/ui'
import Avatar from '@/components/Avatar.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import FilterButton from '@/components/FilterButton.vue'
import Pagination from '@/components/Pagination.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'

const authStore = useAuthStore()
const userStore = useUserStore()
const uiStore = useUiStore()

const searchQuery = ref('')
const permissionFilter = ref('')
const includeDeleted = ref(false)
const currentPage = ref(1)
const pageSize = 20

const deleteModalOpen = ref(false)
const hardDeleteModalOpen = ref(false)
const pendingDeleteId = ref<number | null>(null)
const pendingHardDeleteId = ref<number | null>(null)

onMounted(() => {
  if (authStore.isAdmin) {
    loadUsers()
  }
})

watch(currentPage, () => {
  loadUsers()
})

function loadUsers() {
  userStore.fetchUsers({
    skip: (currentPage.value - 1) * pageSize,
    limit: pageSize,
    username: searchQuery.value || undefined,
    email: searchQuery.value || undefined,
    permission: permissionFilter.value ? Number(permissionFilter.value) : undefined,
    include_deleted: includeDeleted.value
  })
}

function handleSearch() {
  currentPage.value = 1
  loadUsers()
}

function confirmDelete(id: number) {
  pendingDeleteId.value = id
  deleteModalOpen.value = true
}

function confirmHardDelete(id: number) {
  pendingHardDeleteId.value = id
  hardDeleteModalOpen.value = true
}

async function executeDelete() {
  if (pendingDeleteId.value == null) return
  try {
    await userStore.deleteUser(pendingDeleteId.value)
  } catch (error: any) {
    const message = error.response?.data?.message || '注销失败'
    uiStore.showToast(message, 'error')
  }
  deleteModalOpen.value = false
  pendingDeleteId.value = null
}

async function executeHardDelete() {
  if (pendingHardDeleteId.value == null) return
  try {
    await userStore.hardDeleteUser(pendingHardDeleteId.value)
  } catch (error: any) {
    const message = error.response?.data?.message || '删除失败'
    uiStore.showToast(message, 'error')
  }
  hardDeleteModalOpen.value = false
  pendingHardDeleteId.value = null
}

function permLabel(p: number) {
  if (p === 2) return '超管'
  if (p === 1) return '管理员'
  return '用户'
}

function permClass(p: number) {
  if (p === 2) return 'super-admin'
  if (p === 1) return 'admin'
  return 'user'
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.user-admin-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.page-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 32px;
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-select {
  padding: 8px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
  font-family: var(--font-body);
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-secondary);
  cursor: pointer;
}
.admin-table {
  background: var(--text-white);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 24px;
}
.table-row {
  display: grid;
  grid-template-columns: 60px 1.5fr 1.5fr 80px 120px 80px 1fr;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  font-size: 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.table-row.header {
  font-weight: 600;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.02);
}
.table-row:hover:not(.header) {
  background: rgba(0, 0, 0, 0.02);
}
.col-user {
  display: flex;
  align-items: center;
  gap: 8px;
}
.perm-badge {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: var(--radius-pill);
}
.perm-badge.user {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
}
.perm-badge.admin {
  background: rgba(0, 113, 227, 0.15);
  color: var(--apple-blue);
}
.perm-badge.super-admin {
  background: rgba(175, 82, 222, 0.15);
  color: var(--admin-purple);
}
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.active {
  background: var(--success-green);
}
.status-dot.deleted {
  background: var(--text-tertiary);
}
.col-actions {
  display: flex;
  gap: 8px;
}
.action-link {
  font-size: 12px;
  color: var(--link-blue);
  background: transparent;
  border: none;
  cursor: pointer;
}
.action-link.danger {
  color: var(--error-red);
}
.modal-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-family: var(--font-body);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  background: var(--button-default-light);
  color: var(--text-secondary);
}
.modal-btn.danger {
  background: var(--error-red);
  color: var(--text-white);
}
</style>
