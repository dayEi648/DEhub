<template>
  <div class="forum-page">
    <section class="forum-hero">
      <div class="container">
        <h1 class="hero-title">Forum</h1>
        <p class="hero-subtitle">交流与讨论的空间</p>
      </div>
    </section>

    <section class="zones-section">
      <div class="container">
        <div v-if="authStore.isAdmin" class="admin-bar">
          <PrimaryButton @click="openCreateModal">新建分区</PrimaryButton>
        </div>
        <div class="zone-grid">
          <Card
            v-for="zone in forumStore.zones"
            :key="zone.id"
            class="zone-card"
          >
            <div class="zone-header">
              <h3 class="zone-name">{{ zone.zone_name }}</h3>
              <div v-if="canEditZone(zone)" class="zone-admin">
                <button class="action-link" @click.stop="openEditModal(zone)">编辑</button>
                <button v-if="authStore.isAdmin" class="action-link danger" @click.stop="openDeleteZoneModal(zone.id)">删除</button>
              </div>
            </div>
            <p class="zone-desc">{{ zone.description || '暂无描述' }}</p>
            <div class="zone-meta">
              <Avatar :size="24" :src="zone.manager.avatar_url" :name="zone.manager.username" />
              <span>{{ zone.manager.username }}</span>
              <span>浏览量 {{ zone.view_count }}</span>
            </div>
            <div class="zone-actions">
              <button
                class="follow-btn"
                :class="{ followed: isFollowed(zone.id) }"
                @click.stop="toggleFollow(zone.id)"
              >
                {{ isFollowed(zone.id) ? '👁 已关注' : '👁 关注' }}
              </button>
              <PillLink :to="`/forum/${zone.slug}`">进入分区 →</PillLink>
            </div>
          </Card>
        </div>
        <EmptyState v-if="forumStore.zones.length === 0" description="暂无分区" />
      </div>
    </section>

    <!-- 创建分区 Modal -->
    <Modal v-model="showCreateModal" title="新建分区">
      <div class="form-group">
        <label>分区名称</label>
        <input v-model="createForm.zone_name" class="form-input" placeholder="分区名称" />
      </div>
      <div class="form-group">
        <label>Slug</label>
        <input v-model="createForm.slug" class="form-input" placeholder="留空则自动生成" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="createForm.description" class="form-input" rows="2" placeholder="可选" />
      </div>
      <div class="form-group">
        <label>管理者</label>
        <UserSearchSelect v-model="createForm.manager_id" />
        <span class="field-hint">留空则默认将当前用户设为管理者</span>
      </div>
      <template #footer>
        <PrimaryButton @click="createZone">创建</PrimaryButton>
        <PillLink @click="showCreateModal = false">取消</PillLink>
      </template>
    </Modal>

    <!-- 编辑分区 Modal -->
    <Modal v-model="showEditModal" title="编辑分区">
      <div class="form-group">
        <label>分区名称</label>
        <input v-model="editForm.zone_name" class="form-input" placeholder="分区名称" />
      </div>
      <div class="form-group">
        <label>Slug</label>
        <input v-model="editForm.slug" class="form-input" placeholder="slug" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="editForm.description" class="form-input" rows="2" placeholder="可选" />
      </div>
      <div v-if="authStore.isAdmin" class="form-group">
        <label>管理者</label>
        <UserSearchSelect v-model="editForm.manager_id" />
      </div>
      <template #footer>
        <PrimaryButton @click="updateZone">保存</PrimaryButton>
        <PillLink @click="showEditModal = false">取消</PillLink>
      </template>
    </Modal>

    <Modal v-model="showDeleteZoneModal" title="确认删除">
      <p>确认删除该分区？此操作不可撤销。</p>
      <template #footer>
        <button class="action-link danger" @click="confirmDeleteZone">确认删除</button>
        <PillLink @click="showDeleteZoneModal = false">取消</PillLink>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useForumStore } from '@/stores/forum'
import { useFollowStore } from '@/stores/follow'
import { useUiStore } from '@/stores/ui'
import Card from '@/components/Card.vue'
import PillLink from '@/components/PillLink.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import Avatar from '@/components/Avatar.vue'
import UserSearchSelect from '@/components/UserSearchSelect.vue'
import type { ForumZoneResponse } from '@/types'

const authStore = useAuthStore()
const forumStore = useForumStore()
const followStore = useFollowStore()
const uiStore = useUiStore()

const showCreateModal = ref(false)
const showEditModal = ref(false)
const showDeleteZoneModal = ref(false)
const pendingZoneId = ref<number | null>(null)
const editingZoneId = ref<number | null>(null)

const createForm = reactive({
  zone_name: '',
  slug: '',
  description: '',
  manager_id: null as number | null
})

const editForm = reactive({
  zone_name: '',
  slug: '',
  description: '',
  manager_id: null as number | null
})

onMounted(() => {
  forumStore.fetchZones()
  followStore.fetchFollowedZones({ limit: 100 })
})

function canEditZone(zone: ForumZoneResponse): boolean {
  return authStore.isAdmin || zone.manager_id === authStore.user?.id
}

function openCreateModal() {
  createForm.zone_name = ''
  createForm.slug = ''
  createForm.description = ''
  createForm.manager_id = null
  showCreateModal.value = true
}

function openEditModal(zone: ForumZoneResponse) {
  editingZoneId.value = zone.id
  editForm.zone_name = zone.zone_name
  editForm.slug = zone.slug
  editForm.description = zone.description || ''
  editForm.manager_id = zone.manager_id
  showEditModal.value = true
}

async function createZone() {
  if (!createForm.zone_name.trim()) {
    uiStore.showToast('请输入分区名称', 'error')
    return
  }
  try {
    const data: { zone_name: string; slug?: string; description: string | null; manager_id?: number } = {
      zone_name: createForm.zone_name.trim(),
      description: createForm.description.trim() || null
    }
    if (createForm.slug.trim()) {
      data.slug = createForm.slug.trim()
    }
    if (createForm.manager_id !== null) {
      data.manager_id = createForm.manager_id
    }
    await forumStore.createZone(data)
    showCreateModal.value = false
    createForm.zone_name = ''
    createForm.slug = ''
    createForm.description = ''
    createForm.manager_id = null
  } catch (error: any) {
    const message = error.response?.data?.message || '创建失败'
    uiStore.showToast(message, 'error')
  }
}

async function updateZone() {
  if (!editingZoneId.value) return
  if (!editForm.zone_name.trim()) {
    uiStore.showToast('请输入分区名称', 'error')
    return
  }
  try {
    const data: { zone_name?: string; slug?: string; description?: string | null; manager_id?: number } = {}
    if (editForm.zone_name.trim()) {
      data.zone_name = editForm.zone_name.trim()
    }
    if (editForm.slug.trim()) {
      data.slug = editForm.slug.trim()
    }
    data.description = editForm.description.trim() || null
    if (authStore.isAdmin && editForm.manager_id !== null) {
      data.manager_id = editForm.manager_id
    }
    await forumStore.updateZone(editingZoneId.value, data)
    showEditModal.value = false
    editingZoneId.value = null
  } catch (error: any) {
    const message = error.response?.data?.message || '更新失败'
    uiStore.showToast(message, 'error')
  }
}

function openDeleteZoneModal(id: number) {
  pendingZoneId.value = id
  showDeleteZoneModal.value = true
}

function isFollowed(zoneId: number) {
  return followStore.followedZoneIds.includes(zoneId)
}

async function toggleFollow(zoneId: number) {
  try {
    if (isFollowed(zoneId)) {
      await followStore.unfollowZone(zoneId)
    } else {
      await followStore.followZone(zoneId)
    }
  } catch (error: any) {
    const message = error.response?.data?.message || '操作失败'
    uiStore.showToast(message, 'error')
  }
}

async function confirmDeleteZone() {
  showDeleteZoneModal.value = false
  if (pendingZoneId.value !== null) {
    try {
      await forumStore.deleteZone(pendingZoneId.value)
    } catch (error: any) {
      const message = error.response?.data?.message || '删除失败'
      uiStore.showToast(message, 'error')
    }
    pendingZoneId.value = null
  }
}
</script>

<style scoped>
.forum-hero {
  height: 40vh;
  background: var(--bg-black);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.hero-title {
  font-family: var(--font-display);
  font-size: 56px;
  font-weight: 600;
  line-height: 1.07;
  color: var(--text-white);
}
.hero-subtitle {
  font-size: 21px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 8px;
}
.zones-section {
  background: var(--bg-gray);
  padding: 60px 0;
}
.admin-bar {
  margin-bottom: 24px;
}
.zone-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}
@media (max-width: 640px) {
  .zone-grid {
    grid-template-columns: 1fr;
  }
}
.zone-card {
  padding: 32px;
  background: var(--text-white);
}
.zone-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 8px;
}
.zone-name {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 400;
  line-height: 1.14;
  color: var(--text-primary);
}
.zone-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}
.zone-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}
.zone-admin {
  display: none;
  gap: 8px;
}
.zone-header:hover .zone-admin {
  display: flex;
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
.form-group {
  margin-bottom: 16px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}
.form-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
}
.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-tertiary);
}
.zone-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.follow-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}
.follow-btn:hover {
  color: var(--text-secondary);
}
.follow-btn.followed {
  color: var(--apple-blue);
}
</style>
