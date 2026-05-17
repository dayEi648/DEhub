<template>
  <div class="blog-admin-page">
    <div class="container">
      <template v-if="authStore.isSuperAdmin">
        <h1 class="page-title">博客管理后台</h1>

        <div class="stats-grid">
          <Card class="stat-card">
            <div class="stat-value">{{ blogStore.totalPosts }}</div>
            <div class="stat-label">总文章</div>
          </Card>
          <Card class="stat-card">
            <div class="stat-value">{{ publishedCount }}</div>
            <div class="stat-label">已发布</div>
          </Card>
          <Card class="stat-card">
            <div class="stat-value">{{ draftCount }}</div>
            <div class="stat-label">草稿</div>
          </Card>
          <Card class="stat-card">
            <div class="stat-value">{{ deletedCount }}</div>
            <div class="stat-label">已删除</div>
          </Card>
        </div>

        <div class="admin-toolbar">
          <div class="filter-tabs">
            <button
              v-for="tab in statusTabs"
              :key="tab.value"
              class="filter-tab"
              :class="{ active: currentFilter === tab.value }"
              @click="currentFilter = tab.value"
            >
              {{ tab.label }}
            </button>
          </div>
          <input v-model="searchQuery" class="search-input" placeholder="搜索标题" @keydown.enter="handleSearch" />
        </div>

        <div class="admin-table">
          <div class="table-row header">
            <div class="col-id">ID</div>
            <div class="col-title">标题</div>
            <div class="col-category">分类</div>
            <div class="col-status">状态</div>
            <div class="col-views">浏览量</div>
            <div class="col-date">创建时间</div>
            <div class="col-actions">操作</div>
          </div>
          <div
            v-for="post in paginatedPosts"
            :key="post.id"
            class="table-row"
          >
            <div class="col-id">{{ post.id }}</div>
            <div class="col-title">{{ post.title }}</div>
            <div class="col-category">{{ getCategoryName(post.category_id) }}</div>
            <div class="col-status">
              <span class="status-dot" :class="post.status" />
              {{ post.status === 'published' ? '已发布' : '草稿' }}
            </div>
            <div class="col-views">{{ post.view_count }}</div>
            <div class="col-date">{{ formatDate(post.created_at) }}</div>
            <div class="col-actions">
              <PillLink :to="`/blog/edit/${post.slug}`">编辑</PillLink>
              <button
                class="action-link"
                @click="togglePublish(post)"
              >
                {{ post.status === 'published' ? '下线' : '发布' }}
              </button>
              <button class="action-link" @click="handleDelete(post.id)">删除</button>
              <button class="action-link danger" @click="handleHardDelete(post.id)">硬删除</button>
            </div>
          </div>
          <div v-if="paginatedPosts.length === 0" class="table-row empty">
            <div class="col-empty">暂无数据</div>
          </div>
        </div>

        <Pagination
          v-if="filteredTotal > pageSize"
          v-model:current-page="currentPage"
          :total="filteredTotal"
          :page-size="pageSize"
        />

        <div class="category-section">
          <h2 class="section-title">分类管理</h2>
          <div class="admin-table">
            <div class="table-row header">
              <div class="col-id">ID</div>
              <div class="col-title">名称</div>
              <div class="col-title">Slug</div>
              <div class="col-views">文章数</div>
              <div class="col-actions">操作</div>
            </div>
            <div
              v-for="cat in blogStore.categories"
              :key="cat.id"
              class="table-row"
            >
              <div class="col-id">{{ cat.id }}</div>
              <div class="col-title">{{ cat.name }}</div>
              <div class="col-title">{{ cat.slug }}</div>
              <div class="col-views">{{ cat.post_count }}</div>
              <div class="col-actions">
                <button class="action-link" @click="openEditCategory(cat)">编辑</button>
                <button
                  class="action-link danger"
                  @click="cat.post_count === 0 ? blogStore.deleteCategory(cat.id) : uiStore.showToast('该分类下还有文章', 'error')"
                >
                  删除
                </button>
              </div>
            </div>
            <div v-if="blogStore.categories.length === 0" class="table-row empty">
              <div class="col-empty">暂无分类</div>
            </div>
          </div>
          <PrimaryButton class="mt-4" @click="openCreateCategory">新建分类</PrimaryButton>
        </div>

        <!-- 删除确认 Modal -->
        <Modal v-model="showDeleteModal" title="确认删除">
          <p>确定要将这篇文章移至回收站吗？</p>
          <template #footer>
            <PrimaryButton @click="confirmDelete">确认</PrimaryButton>
            <PillLink @click="showDeleteModal = false">取消</PillLink>
          </template>
        </Modal>

        <!-- 硬删除确认 Modal -->
        <Modal v-model="showHardDeleteModal" title="确认彻底删除">
          <p style="color: var(--error-red)">此操作不可恢复，确定要彻底删除这篇文章吗？</p>
          <template #footer>
            <PrimaryButton @click="confirmHardDelete">确认</PrimaryButton>
            <PillLink @click="showHardDeleteModal = false">取消</PillLink>
          </template>
        </Modal>

        <!-- 分类表单 Modal -->
        <Modal v-model="showCategoryModal" :title="editingCategory ? '编辑分类' : '新建分类'">
          <div class="form-group">
            <label>名称</label>
            <input v-model="categoryForm.name" class="form-input" placeholder="分类名称" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="categoryForm.description" class="form-input" placeholder="可选" />
          </div>
          <template #footer>
            <PrimaryButton @click="saveCategory">保存</PrimaryButton>
            <PillLink @click="showCategoryModal = false">取消</PillLink>
          </template>
        </Modal>
      </template>
      <EmptyState v-else description="权限不足，需要超级管理员权限" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
import { useUiStore } from '@/stores/ui'
import Card from '@/components/Card.vue'
import PillLink from '@/components/PillLink.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import Pagination from '@/components/Pagination.vue'
import Modal from '@/components/Modal.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { BlogCategoryWithPostCount } from '@/types'

const authStore = useAuthStore()
const blogStore = useBlogStore()
const uiStore = useUiStore()

const currentFilter = ref<'all' | 'draft' | 'published' | 'deleted'>('all')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = 20

const showDeleteModal = ref(false)
const showHardDeleteModal = ref(false)
const showCategoryModal = ref(false)
const pendingDeleteId = ref<number | null>(null)
const pendingHardDeleteId = ref<number | null>(null)
const editingCategory = ref<BlogCategoryWithPostCount | null>(null)
const categoryForm = reactive({ name: '', description: '' })

const statusTabs = [
  { label: '全部', value: 'all' as const },
  { label: '草稿', value: 'draft' as const },
  { label: '已发布', value: 'published' as const }
]

onMounted(() => {
  if (authStore.isSuperAdmin) {
    blogStore.fetchPosts({ include_unpublished: true })
    blogStore.fetchCategories()
  }
})

watch(currentFilter, () => {
  currentPage.value = 1
})

const publishedCount = computed(() => blogStore.posts.filter((p) => p.status === 'published').length)
const draftCount = computed(() => blogStore.posts.filter((p) => p.status === 'draft').length)

const allFilteredPosts = computed(() => {
  let list = blogStore.posts
  if (currentFilter.value !== 'all') {
    list = list.filter((p) => p.status === currentFilter.value)
  }
  if (searchQuery.value) {
    list = list.filter((p) => p.title.includes(searchQuery.value))
  }
  return list
})

const filteredTotal = computed(() => allFilteredPosts.value.length)

const paginatedPosts = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return allFilteredPosts.value.slice(start, start + pageSize)
})

function getCategoryName(id: number) {
  return blogStore.categories.find((c) => c.id === id)?.name || '未分类'
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}

function handleSearch() {
  currentPage.value = 1
}

async function togglePublish(post: any) {
  try {
    if (post.status === 'published') {
      await blogStore.unpublishPost(post.id)
    } else {
      await blogStore.publishPost(post.id)
    }
  } catch (error: any) {
    const message = error.response?.data?.message || '操作失败'
    uiStore.showToast(message, 'error')
  }
}

function handleDelete(id: number) {
  pendingDeleteId.value = id
  showDeleteModal.value = true
}

async function confirmDelete() {
  if (pendingDeleteId.value !== null) {
    try {
      await blogStore.deletePost(pendingDeleteId.value)
    } catch (error: any) {
      const message = error.response?.data?.message || '删除失败'
      uiStore.showToast(message, 'error')
    }
  }
  showDeleteModal.value = false
  pendingDeleteId.value = null
}

function handleHardDelete(id: number) {
  pendingHardDeleteId.value = id
  showHardDeleteModal.value = true
}

async function confirmHardDelete() {
  if (pendingHardDeleteId.value !== null) {
    try {
      await blogStore.hardDeletePost(pendingHardDeleteId.value)
    } catch (error: any) {
      const message = error.response?.data?.message || '彻底删除失败'
      uiStore.showToast(message, 'error')
    }
  }
  showHardDeleteModal.value = false
  pendingHardDeleteId.value = null
}

function openCreateCategory() {
  editingCategory.value = null
  categoryForm.name = ''
  categoryForm.description = ''
  showCategoryModal.value = true
}

function openEditCategory(cat: BlogCategoryWithPostCount) {
  editingCategory.value = cat
  categoryForm.name = cat.name
  categoryForm.description = cat.description || ''
  showCategoryModal.value = true
}

async function saveCategory() {
  if (!categoryForm.name) {
    uiStore.showToast('名称不能为空', 'error')
    return
  }
  try {
    if (editingCategory.value) {
      await blogStore.updateCategory(editingCategory.value.id, { name: categoryForm.name, description: categoryForm.description || null })
    } else {
      await blogStore.createCategory({ name: categoryForm.name, description: categoryForm.description || null })
    }
    showCategoryModal.value = false
  } catch (error: any) {
    const message = error.response?.data?.message || '保存失败'
    uiStore.showToast(message, 'error')
  }
}
</script>

<style scoped>
.blog-admin-page {
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
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
.stat-card {
  padding: 24px;
  text-align: center;
}
.stat-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary);
}
.stat-label {
  font-size: 14px;
  color: var(--text-tertiary);
  margin-top: 4px;
}
.admin-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-tabs {
  display: flex;
  gap: 4px;
}
.filter-tab {
  padding: 6px 14px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
}
.filter-tab.active {
  background: var(--text-primary);
  color: var(--text-white);
}
.search-input {
  padding: 8px 14px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  outline: none;
}
.danger-link {
  font-size: 14px;
  color: var(--error-red);
  background: transparent;
  border: none;
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
  grid-template-columns: 60px 2fr 1fr 100px 80px 120px 1.5fr;
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
.table-row.empty {
  display: block;
  text-align: center;
  color: var(--text-tertiary);
  padding: 24px;
}
.col-empty {
  width: 100%;
}
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.status-dot.draft {
  background: var(--text-tertiary);
}
.status-dot.published {
  background: var(--success-green);
}
.status-dot.deleted {
  background: var(--error-red);
}
.col-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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
.category-section {
  margin-top: 48px;
}
.section-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 400;
  margin-bottom: 24px;
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
.mt-4 {
  margin-top: 16px;
}
</style>
