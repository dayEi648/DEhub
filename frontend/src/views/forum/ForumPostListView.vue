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
        <ForumPostCard
          v-for="post in forumStore.posts"
          :key="post.id"
          :post="post"
          @click="$router.push(`/forum/post/${post.id}`)"
        />
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
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { useForumStore } from '@/stores/forum'
import { useUiStore } from '@/stores/ui'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'
import ForumPostCard from '@/components/ForumPostCard.vue'

const route = useRoute()
const router = useRouter()
const forumStore = useForumStore()
const uiStore = useUiStore()

const currentSort = ref<'created' | 'view'>('created')
const currentPage = ref(1)
const pageSize = 20

const currentZoneId = ref<number | undefined>(undefined)

onMounted(async () => {
  await loadZoneAndPosts()
})

onBeforeRouteUpdate(async (to) => {
  const slug = to.params.zoneSlug as string
  if (slug !== route.params.zoneSlug) {
    currentPage.value = 1
    currentSort.value = 'created'
    await loadZoneAndPosts(slug)
  }
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

async function loadZoneAndPosts(slug?: string) {
  const targetSlug = slug || (route.params.zoneSlug as string)
  let zone = forumStore.zones.find((z) => z.slug === targetSlug)
  if (!zone) {
    try {
      await forumStore.fetchZones()
    } catch (error: any) {
      const message = error.response?.data?.message || '加载分区失败'
      uiStore.showToast(message, 'error')
      return
    }
    zone = forumStore.zones.find((z) => z.slug === targetSlug)
  }
  if (zone) {
    forumStore.currentZone = zone
    currentZoneId.value = zone.id
    try {
      await forumStore.fetchPosts({
        zone_id: zone.id,
        sort_by: currentSort.value,
        skip: (currentPage.value - 1) * pageSize,
        limit: pageSize
      })
    } catch (error: any) {
      const message = error.response?.data?.message || '加载帖子失败'
      uiStore.showToast(message, 'error')
    }
  } else {
    router.push('/404')
  }
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

</style>
