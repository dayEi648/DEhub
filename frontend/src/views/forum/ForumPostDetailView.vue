<template>
  <div class="forum-detail-page">
    <div v-if="forumStore.currentPost" class="container">
      <Card class="post-card">
        <h1 class="post-title">{{ forumStore.currentPost.title }}</h1>
        <div class="post-author">
          <Avatar :size="40" :src="forumStore.currentPost.user.avatar_url" :name="forumStore.currentPost.user.username" />
          <div class="author-info">
            <span class="author-name">{{ forumStore.currentPost.user.username }}</span>
            <span class="post-date">{{ formatDate(forumStore.currentPost.created_at) }}</span>
            <span>👁 {{ forumStore.currentPost.view_count }}</span>
            <span>💬 {{ forumStore.currentPost.reply_count }}</span>
            <button
              class="favorite-btn"
              :class="{ favorited: isFavorited }"
              @click="toggleFavorite"
            >
              {{ isFavorited ? '⭐ 已收藏' : '☆ 收藏' }}
            </button>
          </div>
        </div>
        <div class="post-body">{{ forumStore.currentPost.content }}</div>
        <div v-if="canEditPost || canDeletePost" class="post-actions">
          <PillLink v-if="canEditPost" :to="`/forum/post/edit/${forumStore.currentPost.id}`">编辑</PillLink>
          <button v-if="canDeletePost" class="action-link danger" @click="showDeletePostModal = true">删除</button>
        </div>
      </Card>

      <Card class="replies-card">
        <h2 class="replies-title">回复 ({{ forumStore.totalReplies }})</h2>
        <div class="reply-input-area">
          <textarea v-model="replyContent" class="reply-textarea" rows="3" placeholder="写下你的回复..." />
          <div class="reply-actions">
            <PrimaryButton @click="submitReply">回复</PrimaryButton>
          </div>
        </div>
        <div class="reply-list">
          <div v-for="reply in forumStore.replies" :key="reply.id" class="reply-item">
            <Avatar :size="32" :src="reply.user.avatar_url" :name="reply.user.username" />
            <div class="reply-body">
              <div class="reply-meta">
                <span class="reply-author">{{ reply.user.username }}</span>
                <span class="reply-time">{{ formatDate(reply.created_at) }}</span>
              </div>
              <p class="reply-content">{{ reply.content }}</p>
              <div class="reply-actions-bar">
              <button class="action-link" @click="toggleReplyComments(reply.id)">
                {{ expandedReplyComments.has(reply.id) ? '收起回复' : '查看更多回复' }}
              </button>
              <button v-if="canManageReply(reply.user_id)" class="action-link danger" @click="openDeleteReplyModal(reply.id)">删除</button>
            </div>
            <ForumReplyComments v-if="expandedReplyComments.has(reply.id)" :reply-id="reply.id" />
          </div>
        </div>
        <Pagination
          v-if="forumStore.totalReplies > pageSize"
          v-model:current-page="currentPage"
          :total="forumStore.totalReplies"
          :page-size="pageSize"
        />
      </Card>

      <div class="back-link">
        <PillLink :to="forumStore.currentZone ? `/forum/${forumStore.currentZone.slug}` : '/forum'">← 返回帖子列表</PillLink>
      </div>
    </div>

    <!-- Delete Post Modal -->
    <Modal v-model="showDeletePostModal" title="确认删除">
      <p>确认删除此帖子？此操作不可撤销。</p>
      <template #footer>
        <button class="action-link danger" @click="confirmDeletePost">确认删除</button>
        <PillLink @click="showDeletePostModal = false">取消</PillLink>
      </template>
    </Modal>

    <!-- Delete Reply Modal -->
    <Modal v-model="showDeleteReplyModal" title="确认删除">
      <p>确认删除此回复？此操作不可撤销。</p>
      <template #footer>
        <button class="action-link danger" @click="confirmDeleteReply">确认删除</button>
        <PillLink @click="showDeleteReplyModal = false">取消</PillLink>
      </template>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter, onBeforeRouteUpdate } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useForumStore } from '@/stores/forum'
import { useFavoriteStore } from '@/stores/favorite'
import { useUiStore } from '@/stores/ui'
import Card from '@/components/Card.vue'
import Avatar from '@/components/Avatar.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import PillLink from '@/components/PillLink.vue'
import Pagination from '@/components/Pagination.vue'
import Modal from '@/components/Modal.vue'
import ForumReplyComments from '@/components/ForumReplyComments.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const forumStore = useForumStore()
const favoriteStore = useFavoriteStore()
const uiStore = useUiStore()

const replyContent = ref('')
const currentPage = ref(1)
const pageSize = 20

const showDeletePostModal = ref(false)
const showDeleteReplyModal = ref(false)
const pendingReplyId = ref<number | null>(null)

const postId = computed(() => Number(route.params.postId))

const isFavorited = computed(() => {
  if (!forumStore.currentPost) return false
  return favoriteStore.forumPostFavoriteIds.includes(forumStore.currentPost.id)
})

async function toggleFavorite() {
  if (!forumStore.currentPost) return
  try {
    if (isFavorited.value) {
      await favoriteStore.unfavoriteForumPost(forumStore.currentPost.id)
    } else {
      await favoriteStore.favoriteForumPost(forumStore.currentPost.id)
    }
  } catch (error: any) {
    const message = error.response?.data?.message || '操作失败'
    uiStore.showToast(message, 'error')
  }
}

const canEditPost = computed(() => {
  if (!authStore.user || !forumStore.currentPost) return false
  const isAuthor = authStore.user.id === forumStore.currentPost.user_id
  const isAdmin = authStore.isAdmin
  return isAuthor || isAdmin
})

const canDeletePost = computed(() => {
  if (!authStore.user || !forumStore.currentPost) return false
  const isAuthor = authStore.user.id === forumStore.currentPost.user_id
  const isAdmin = authStore.isAdmin
  const isZoneManager = forumStore.currentZone?.manager_id === authStore.user.id
  return isAuthor || isAdmin || isZoneManager
})

function canManageReply(userId: number) {
  if (!authStore.user || !forumStore.currentPost) return false
  const isAuthor = authStore.user.id === userId
  const isAdmin = authStore.isAdmin
  const isZoneManager = forumStore.currentZone?.manager_id === authStore.user.id
  return isAuthor || isAdmin || isZoneManager
}

const expandedReplyComments = ref<Set<number>>(new Set())

function toggleReplyComments(replyId: number) {
  if (expandedReplyComments.value.has(replyId)) {
    expandedReplyComments.value.delete(replyId)
  } else {
    expandedReplyComments.value.add(replyId)
  }
}

onMounted(() => {
  loadPostData(postId.value)
})

onBeforeRouteUpdate((to) => {
  const newPostId = Number(to.params.postId)
  if (newPostId !== postId.value) {
    currentPage.value = 1
    replyContent.value = ''
    loadPostData(newPostId)
  }
})

watch(currentPage, () => {
  forumStore.fetchReplies(postId.value, {
    skip: (currentPage.value - 1) * pageSize,
    limit: pageSize
  })
})

async function loadPostData(id: number) {
  try {
    const post = await forumStore.fetchPostById(id)
    if (post?.zone_id) {
      await forumStore.fetchZoneById(post.zone_id)
    }
    await forumStore.fetchReplies(id, { limit: pageSize })
    // 预拉取收藏列表，用于判断当前帖子收藏状态
    await favoriteStore.fetchForumPostFavorites({ limit: 100 })
  } catch (error: any) {
    if (error.response?.status === 404) {
      router.push('/404')
    } else {
      const message = error.response?.data?.message || '加载帖子失败'
      uiStore.showToast(message, 'error')
    }
  }
}

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}

async function submitReply() {
  if (!replyContent.value.trim()) return
  try {
    await forumStore.createReply(postId.value, replyContent.value.trim())
    replyContent.value = ''
  } catch (error: any) {
    const message = error.response?.data?.message || '回复失败，请重试'
    uiStore.showToast(message, 'error')
  }
}

async function confirmDeletePost() {
  showDeletePostModal.value = false
  try {
    await forumStore.deletePost(postId.value)
    router.push(forumStore.currentZone ? `/forum/${forumStore.currentZone.slug}` : '/forum')
  } catch (error: any) {
    const message = error.response?.data?.message || '删除失败'
    uiStore.showToast(message, 'error')
  }
}

function openDeleteReplyModal(replyId: number) {
  pendingReplyId.value = replyId
  showDeleteReplyModal.value = true
}

async function confirmDeleteReply() {
  showDeleteReplyModal.value = false
  if (pendingReplyId.value !== null) {
    try {
      await forumStore.deleteReply(pendingReplyId.value)
    } catch (error: any) {
      const message = error.response?.data?.message || '删除失败'
      uiStore.showToast(message, 'error')
    }
    pendingReplyId.value = null
  }
}
</script>

<style scoped>
.forum-detail-page {
  background: var(--bg-gray);
  min-height: calc(100vh - 48px);
  padding: 40px 0;
}
.post-card {
  padding: 40px;
  margin-bottom: 24px;
}
.post-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}
.post-author {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.author-info {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: var(--text-tertiary);
}
.author-name {
  font-weight: 600;
  color: var(--text-primary);
}
.post-body {
  font-size: 17px;
  line-height: 1.74;
  color: var(--text-primary);
  margin-bottom: 24px;
}
.post-actions {
  display: flex;
  gap: 12px;
}
.replies-card {
  padding: 32px;
  margin-bottom: 24px;
}
.replies-title {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  margin-bottom: 20px;
}
.reply-input-area {
  margin-bottom: 24px;
}
.reply-textarea {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  background: var(--button-default-light);
  border: 3px solid rgba(0, 0, 0, 0.04);
  border-radius: var(--radius-lg);
  resize: vertical;
  outline: none;
  margin-bottom: 12px;
}
.reply-actions {
  display: flex;
  justify-content: flex-end;
}
.reply-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.reply-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.reply-body {
  flex: 1;
}
.reply-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
}
.reply-author {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.reply-time {
  font-size: 12px;
  color: var(--text-tertiary);
}
.reply-content {
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-secondary);
}
.reply-actions-bar {
  margin-top: 8px;
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
.back-link {
  text-align: center;
}
.favorite-btn {
  background: transparent;
  border: none;
  font-size: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}
.favorite-btn:hover {
  color: var(--text-secondary);
}
.favorite-btn.favorited {
  color: #f5a623;
}
</style>
