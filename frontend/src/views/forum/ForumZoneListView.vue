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
          <PrimaryButton @click="showZoneModal = true">新建分区</PrimaryButton>
        </div>
        <div class="zone-grid">
          <Card
            v-for="zone in forumStore.zones"
            :key="zone.id"
            class="zone-card"
          >
            <div class="zone-header">
              <h3 class="zone-name">{{ zone.zone_name }}</h3>
              <div v-if="authStore.isAdmin" class="zone-admin">
                <button class="action-link" @click.stop="editZone(zone)">编辑</button>
                <button class="action-link danger" @click.stop="forumStore.deleteZone(zone.id)">删除</button>
              </div>
            </div>
            <p class="zone-desc">{{ zone.description || '暂无描述' }}</p>
            <div class="zone-meta">
              <Avatar :size="24" :src="zone.manager.avatar_url" :name="zone.manager.username" />
              <span>{{ zone.manager.username }}</span>
              <span>浏览量 {{ zone.view_count }}</span>
            </div>
            <PillLink :to="`/forum/${zone.slug}`">进入分区 →</PillLink>
          </Card>
        </div>
        <EmptyState v-if="forumStore.zones.length === 0" description="暂无分区" />
      </div>
    </section>

    <Modal v-model="showZoneModal" title="新建分区">
      <div class="form-group">
        <label>分区名称</label>
        <input v-model="newZone.zone_name" class="form-input" placeholder="分区名称" />
      </div>
      <div class="form-group">
        <label>Slug</label>
        <input v-model="newZone.slug" class="form-input" placeholder="url-slug" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="newZone.description" class="form-input" rows="2" placeholder="可选" />
      </div>
      <template #footer>
        <PrimaryButton @click="createZone">创建</PrimaryButton>
        <PillLink @click="showZoneModal = false">取消</PillLink>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useForumStore } from '@/stores/forum'
import Card from '@/components/Card.vue'
import PillLink from '@/components/PillLink.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import EmptyState from '@/components/EmptyState.vue'
import Modal from '@/components/Modal.vue'
import Avatar from '@/components/Avatar.vue'
import type { ForumZoneResponse } from '@/types'

const authStore = useAuthStore()
const forumStore = useForumStore()

const showZoneModal = ref(false)
const newZone = reactive({ zone_name: '', slug: '', description: '' })

onMounted(() => {
  forumStore.fetchZones()
})

function createZone() {
  forumStore.createZone({ ...newZone })
  showZoneModal.value = false
  newZone.zone_name = ''
  newZone.slug = ''
  newZone.description = ''
}

function editZone(zone: ForumZoneResponse) {
  const name = prompt('新名称', zone.zone_name)
  const slug = prompt('新 Slug', zone.slug)
  if (name && slug) {
    forumStore.updateZone(zone.id, { zone_name: name, slug })
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
</style>
