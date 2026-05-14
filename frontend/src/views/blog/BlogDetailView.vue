<template>
  <div class="blog-detail-page">
    <div v-if="blogStore.currentPost" class="container">
      <img
        v-if="blogStore.currentPost.cover_image_url"
        :src="blogStore.currentPost.cover_image_url"
        class="post-cover"
      />
      <h1 class="post-title">{{ blogStore.currentPost.title }}</h1>
      <div class="post-meta">
        <PillLink :to="`/blog?category=${blogStore.currentPost.category_id}`">
          {{ getCategoryName(blogStore.currentPost.category_id) }}
        </PillLink>
        <span>发布于 {{ formatDate(blogStore.currentPost.created_at) }}</span>
        <span>更新于 {{ formatDate(blogStore.currentPost.updated_at) }}</span>
        <span>👁 {{ blogStore.currentPost.view_count }}</span>
      </div>
      <MarkdownRenderer :content="blogStore.currentPost.content_md" />
      <div v-if="blogStore.currentPost.tags.length" class="post-tags">
        <span
          v-for="tag in blogStore.currentPost.tags"
          :key="tag"
          class="post-tag"
          @click="$router.push(`/blog?tag=${encodeURIComponent(tag)}`)"
        >
          {{ tag }}
        </span>
      </div>

      <div v-if="authStore.isSuperAdmin" class="admin-bar">
        <span class="status-badge" :class="blogStore.currentPost.status">
          <span class="status-dot" :class="blogStore.currentPost.status" />
          {{ blogStore.currentPost.status === 'published' ? '已发布' : '草稿' }}
        </span>
        <PillLink :to="`/blog/edit/${blogStore.currentPost.slug}`">编辑</PillLink>
        <button
          class="action-link"
          @click="togglePublish"
        >
          {{ blogStore.currentPost.status === 'published' ? '下线' : '发布' }}
        </button>
        <button class="action-link danger" @click="showDeleteModal = true">删除</button>
      </div>

      <div class="neighbor-nav">
        <div v-if="blogStore.currentPost.prev_post" class="neighbor prev" @click="$router.push(`/blog/${blogStore.currentPost.prev_post.slug}`)">
          <span class="neighbor-label">← 上一篇</span>
          <span class="neighbor-title">{{ blogStore.currentPost.prev_post.title }}</span>
        </div>
        <div v-if="blogStore.currentPost.next_post" class="neighbor next" @click="$router.push(`/blog/${blogStore.currentPost.next_post.slug}`)">
          <span class="neighbor-label">下一篇 →</span>
          <span class="neighbor-title">{{ blogStore.currentPost.next_post.title }}</span>
        </div>
      </div>

      <CommentSection
        target-type="blog_post"
        :target-id="blogStore.currentPost.id"
      />
    </div>
  </div>

  <!-- 删除确认 Modal -->
  <Modal v-model="showDeleteModal" title="确认删除">
    <p>确定要删除这篇文章吗？此操作不可撤销。</p>
    <template #footer>
      <PillLink @click="showDeleteModal = false">取消</PillLink>
      <PrimaryButton @click="confirmDelete">确认删除</PrimaryButton>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
import { useUiStore } from '@/stores/ui'
import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import PillLink from '@/components/PillLink.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import CommentSection from '@/components/CommentSection.vue'
import Modal from '@/components/Modal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const blogStore = useBlogStore()
const uiStore = useUiStore()

const showDeleteModal = ref(false)

async function loadPost() {
  const slug = route.params.slug as string
  if (!slug) return
  try {
    await blogStore.fetchPostBySlug(slug)
  } catch (error: any) {
    if (error.response?.status === 404) {
      router.push('/404')
    }
  }
}

async function togglePublish() {
  if (!blogStore.currentPost) return
  try {
    if (blogStore.currentPost.status === 'published') {
      await blogStore.unpublishPost(blogStore.currentPost.id)
    } else {
      await blogStore.publishPost(blogStore.currentPost.id)
    }
  } catch (error: any) {
    const message = error.response?.data?.message || '操作失败'
    uiStore.showToast(message, 'error')
  }
}

onMounted(loadPost)

watch(() => route.params.slug, loadPost)

function getCategoryName(id: number) {
  return blogStore.categories.find((c) => c.id === id)?.name || '未分类'
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}

async function confirmDelete() {
  showDeleteModal.value = false
  if (!blogStore.currentPost) return
  try {
    await blogStore.deletePost(blogStore.currentPost.id)
    router.push('/blog')
  } catch (error: any) {
    const message = error.response?.data?.message || '删除失败'
    uiStore.showToast(message, 'error')
  }
}
</script>

<style scoped>
.blog-detail-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.post-cover {
  width: 100%;
  max-height: 480px;
  object-fit: cover;
  border-radius: var(--radius-md);
  margin-bottom: 32px;
}
.post-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  line-height: 1.1;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.post-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--text-tertiary);
  margin-bottom: 32px;
  flex-wrap: wrap;
}
.post-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 24px 0;
}
.post-tag {
  padding: 4px 10px;
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
.admin-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-gray);
  border-radius: var(--radius-md);
  margin: 24px 0;
  flex-wrap: wrap;
}
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  font-size: 12px;
  border-radius: var(--radius-pill);
}
.status-badge.draft {
  background: rgba(0, 0, 0, 0.06);
  color: var(--text-secondary);
}
.status-badge.published {
  background: rgba(52, 199, 89, 0.15);
  color: var(--success-green);
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-dot.draft {
  background: var(--text-tertiary);
}
.status-dot.published {
  background: var(--success-green);
}
.action-link {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--link-blue);
  cursor: pointer;
}
.action-link.danger {
  color: var(--error-red);
}
.neighbor-nav {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  padding: 24px;
  background: var(--bg-gray);
  border-radius: var(--radius-md);
  margin: 24px 0;
}
.neighbor {
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.neighbor.prev {
  text-align: left;
}
.neighbor.next {
  text-align: right;
}
.neighbor-label {
  font-size: 12px;
  color: var(--text-tertiary);
}
.neighbor-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
