<template>
  <div class="blog-list-page">
    <div class="container">
      <div class="filter-bar">
        <div class="category-tabs">
          <button
            class="category-tab"
            :class="{ active: !currentCategory }"
            @click="selectCategory(undefined)"
          >
            全部
          </button>
          <button
            v-for="cat in blogStore.categories"
            :key="cat.id"
            class="category-tab"
            :class="{ active: currentCategory === cat.id }"
            @click="selectCategory(cat.id)"
          >
            {{ cat.name }}
          </button>
        </div>
        <div class="filter-right">
          <FilterButton
            v-model="searchQuery"
            as-input
            placeholder="搜索文章标题"
            @enter="handleSearch"
          />
          <template v-if="authStore.isSuperAdmin">
            <PrimaryButton @click="$router.push('/blog/new')">新建文章</PrimaryButton>
            <PillLink to="/blog/admin">管理后台</PillLink>
          </template>
        </div>
      </div>

      <div class="post-grid">
        <Card
          v-for="post in blogStore.posts"
          :key="post.id"
          class="post-card"
          @click="$router.push(`/blog/${post.slug}`)"
        >
          <img v-if="post.cover_image_url" :src="post.cover_image_url" class="post-cover" />
          <div class="post-body">
            <h3 class="post-title">{{ post.title }}</h3>
            <p class="post-summary">{{ post.summary || '暂无摘要' }}</p>
            <div class="post-meta">
              <span class="post-category">{{ post.category?.name || '未分类' }}</span>
              <span class="post-date">{{ formatDate(post.created_at) }}</span>
              <span class="post-views">👁 {{ post.view_count }}</span>
            </div>
            <div v-if="post.tags.length" class="post-tags">
              <span
                v-for="tag in post.tags"
                :key="tag"
                class="post-tag"
                @click.stop="selectTag(tag)"
              >
                {{ tag }}
              </span>
            </div>
          </div>
        </Card>
      </div>

      <EmptyState v-if="blogStore.posts.length === 0" description="没有找到文章" />

      <Pagination
        v-if="blogStore.totalPosts > pageSize"
        v-model:current-page="currentPage"
        :total="blogStore.totalPosts"
        :page-size="pageSize"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
import { useUiStore } from '@/stores/ui'
import Card from '@/components/Card.vue'
import FilterButton from '@/components/FilterButton.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const blogStore = useBlogStore()
const uiStore = useUiStore()

const currentCategory = ref<number | undefined>(undefined)
const currentTag = ref<string | undefined>(undefined)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 20

function syncUrlQuery() {
  const query: Record<string, any> = {}
  if (currentCategory.value) query.category = currentCategory.value
  if (currentTag.value) query.tag = currentTag.value
  if (searchQuery.value) query.q = searchQuery.value
  if (currentPage.value > 1) query.page = currentPage.value
  router.replace({ query })
}

function loadFromUrl() {
  const { category, tag, q, page } = route.query
  currentCategory.value = category ? Number(category) : undefined
  currentTag.value = tag ? String(tag) : undefined
  searchQuery.value = q ? String(q) : ''
  currentPage.value = page ? Number(page) : 1
}

async function fetchData() {
  try {
    await blogStore.fetchPosts({
      category_id: currentCategory.value,
      tag: currentTag.value,
      q: searchQuery.value || undefined,
      skip: (currentPage.value - 1) * pageSize,
      limit: pageSize
    })
  } catch (error: any) {
    const message = error.response?.data?.message || '加载文章列表失败'
    uiStore.showToast(message, 'error')
  }
}

function selectCategory(id: number | undefined) {
  currentCategory.value = id
  currentTag.value = undefined
  currentPage.value = 1
  syncUrlQuery()
}

function selectTag(tag: string) {
  currentTag.value = tag
  currentCategory.value = undefined
  currentPage.value = 1
  syncUrlQuery()
}

function handleSearch() {
  currentPage.value = 1
  syncUrlQuery()
}

onMounted(() => {
  loadFromUrl()
  fetchData()
  blogStore.fetchCategories()
})

watch(
  () => route.query,
  () => {
    loadFromUrl()
    fetchData()
  }
)

watch(currentPage, () => {
  syncUrlQuery()
})

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.blog-list-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.category-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.category-tab {
  padding: 6px 14px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.category-tab.active {
  color: var(--apple-blue);
  border-bottom-color: var(--apple-blue);
}
.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.post-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}
@media (max-width: 640px) {
  .post-grid {
    grid-template-columns: 1fr;
  }
}
.post-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.post-card:hover {
  transform: translateY(-2px);
}
.post-cover {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
}
.post-body {
  padding: 20px;
}
.post-title {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 700;
  line-height: 1.19;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.post-summary {
  font-size: 14px;
  color: var(--text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}
.post-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 8px;
}
.post-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.post-tag {
  padding: 2px 8px;
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.2s;
}
.post-tag:hover {
  background: rgba(0, 0, 0, 0.08);
}
</style>
