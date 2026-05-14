<template>
  <div class="forum-posts-page">
    <div class="container">
      <div class="zone-header-bar">
        <div>
          <h1 class="zone-title">{{ forumStore.currentZone?.zone_name || '帖子列表' }}</h1>
          <p class="zone-desc">{{ forumStore.currentZone?.description || '' }}</p>
        </div>
        <PillLink to="/forum">← 所有分区</PillLink>
      </div>

      <div class="toolbar">
        <div class="sort-tabs">
          <button
            class="sort-tab"
            :class="{ active: currentSort === 'created' }"
            @click="currentSort = 'created'"
          >
            最新
          </button>
          <button
            class="sort-tab"
            :class="{ active: currentSort === 'view' }"
            @click="currentSort = 'view'"
          >
            最热
          </button>
        </div>
        <PrimaryButton @click="$router.push(`/forum/post/new?zoneId=${currentZoneId}`)">发表帖子</PrimaryButton>
      </div>

      <div class="post-list">
        <Card
          v-for="post in forumStore.posts"
          :key="post.id"
          class="post-item"
          @click="$router.push(`/forum/post/${post.id}`)"
        >
          <Avatar :size="40" :src="post.user.avatar_url" :name="post.user.username" />
          <div class="post-content">
            <h3 class="post-title">{{ post.title }}</h3>
            <p class="post-excerpt">{{ post.content.slice(0, 120) }}...</p>
            <div class="post-meta">
              <span>{{ post.user.username }}</span>
              <span>{{ formatDate(post.created_at) }}</span>
              <span>👁 {{ post.view_count }}</span>
              <span>💬 {{ post.reply_count }}</span>
            </div>
          </div>
        </Card>
      </div>

      <EmptyState v-if="forumStore.posts.length === 0" description="该分区暂无帖子" />

      <Pagination
        v-if="forumStore.totalPosts > pageSize"
        v-model:current-page="currentPage"
        :total="forumStore.totalPosts"
        :page-size="pageSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useForumStore } from '@/stores/forum'
import Card from '@/components/Card.vue'
import Avatar from '@/components/Avatar.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'

const route = useRoute()
const forumStore = useForumStore()

const currentSort = ref<'created' | 'view'>('created')
const currentPage = ref(1)
const pageSize = 20

const currentZoneId = ref<number | undefined>(undefined)

onMounted(async () => {
  await loadZoneAndPosts()
})

watch([currentSort, currentPage], () => {
  if (currentZoneId.value) {
    forumStore.fetchPosts({
      zone_id: currentZoneId.value,
      sort_by: currentSort.value,
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize
    })
  }
})

async function loadZoneAndPosts() {
  const slug = route.params.zoneSlug as string
  let zone = forumStore.zones.find((z) => z.slug === slug)
  if (!zone) {
    await forumStore.fetchZones()
    zone = forumStore.zones.find((z) => z.slug === slug)
  }
  if (zone) {
    forumStore.currentZone = zone
    currentZoneId.value = zone.id
    forumStore.fetchPosts({
      zone_id: zone.id,
      sort_by: currentSort.value,
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize
    })
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.forum-posts-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.zone-header-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}
.zone-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
}
.zone-desc {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.sort-tabs {
  display: flex;
  gap: 4px;
}
.sort-tab {
  padding: 6px 14px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
}
.sort-tab.active {
  background: var(--text-primary);
  color: var(--text-white);
}
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}
.post-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s;
}
.post-item:hover {
  transform: translateY(-1px);
}
.post-content {
  flex: 1;
}
.post-title {
  font-size: 21px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.post-excerpt {
  font-size: 14px;
  color: var(--text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}
.post-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
