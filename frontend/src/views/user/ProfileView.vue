<template>
  <div class="profile-page">
    <section class="profile-hero">
      <div class="container hero-content">
        <ImageUploader
          :preview-url="previewAvatar || authStore.user?.avatar_url"
          :name="authStore.user?.username || ''"
          :size="160"
          @select="handleFileSelect"
        />
        <h1 class="profile-name">{{ authStore.user?.username }}</h1>
        <span class="permission-badge" :class="permissionClass">{{ permissionLabel }}</span>
      </div>
    </section>

    <section class="profile-form-section">
      <div class="container">
        <div class="profile-tabs">
          <button class="profile-tab" :class="{ active: activeTab === 'profile' }" @click="switchTab('profile')">
            个人资料
          </button>
          <button class="profile-tab" :class="{ active: activeTab === 'blog-favorites' }" @click="switchTab('blog-favorites')">
            博客收藏 ({{ favoriteStore.totalBlogFavorites }})
          </button>
          <button class="profile-tab" :class="{ active: activeTab === 'forum-favorites' }" @click="switchTab('forum-favorites')">
            论坛收藏 ({{ favoriteStore.totalForumPostFavorites }})
          </button>
          <button class="profile-tab" :class="{ active: activeTab === 'zone-follows' }" @click="switchTab('zone-follows')">
            关注分区 ({{ followStore.totalFollowedZones }})
          </button>
        </div>

        <!-- 个人资料 -->
        <div v-if="activeTab === 'profile'" class="profile-form">
          <div class="form-group">
            <label>用户名</label>
            <FilterButton as-input v-model="form.username" placeholder="用户名" />
            <span v-if="errors.username" class="field-error">{{ errors.username }}</span>
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <FilterButton as-input v-model="form.email" placeholder="邮箱" />
            <span v-if="errors.email" class="field-error">{{ errors.email }}</span>
          </div>
          <div class="form-group">
            <label>个人简介</label>
            <textarea v-model="form.personal_profile" class="form-input" rows="4" />
            <span v-if="errors.personal_profile" class="field-error">{{ errors.personal_profile }}</span>
          </div>
          <PrimaryButton @click="handleSave">保存更改</PrimaryButton>

          <div class="password-section">
            <div class="section-toggle" @click="togglePasswordSection">
              {{ showPassword ? '收起' : '修改密码' }}
            </div>
            <div v-if="showPassword" class="password-form">
              <div class="form-group">
                <label>旧密码</label>
                <input v-model="passwordForm.oldPassword" type="password" class="form-input" placeholder="请输入旧密码" />
                <span v-if="errors.oldPassword" class="field-error">{{ errors.oldPassword }}</span>
              </div>
              <div class="form-group">
                <label>新密码</label>
                <input v-model="passwordForm.newPassword" type="password" class="form-input" placeholder="6-128 位字符" />
                <span v-if="errors.newPassword" class="field-error">{{ errors.newPassword }}</span>
              </div>
              <div class="form-group">
                <label>确认新密码</label>
                <input v-model="passwordForm.confirmPassword" type="password" class="form-input" placeholder="再次输入新密码" />
                <span v-if="errors.confirmPassword" class="field-error">{{ errors.confirmPassword }}</span>
              </div>
              <PrimaryButton @click="handleChangePassword">确认修改</PrimaryButton>
            </div>
          </div>
        </div>

        <!-- 博客收藏 -->
        <div v-else-if="activeTab === 'blog-favorites'" class="favorites-panel">
          <div v-if="favoriteStore.blogFavorites.length" class="post-grid">
            <Card
              v-for="post in favoriteStore.blogFavorites"
              :key="post.id"
              class="post-card"
              @click="$router.push(`/blog/${post.slug}`)"
            >
              <img v-if="post.cover_image_url" :src="post.cover_image_url" class="post-cover" />
              <div class="post-body">
                <h3 class="post-title">{{ post.title }}</h3>
                <p class="post-summary">{{ post.summary || '暂无摘要' }}</p>
                <div class="post-meta">
                  <span class="post-date">{{ formatDate(post.created_at) }}</span>
                  <span class="post-views">👁 {{ post.view_count }}</span>
                </div>
              </div>
            </Card>
          </div>
          <EmptyState v-else description="暂无收藏的博客文章" />
          <Pagination
            v-if="favoriteStore.totalBlogFavorites > pageSize"
            v-model:current-page="blogFavPage"
            :total="favoriteStore.totalBlogFavorites"
            :page-size="pageSize"
          />
        </div>

        <!-- 论坛收藏 -->
        <div v-else-if="activeTab === 'forum-favorites'" class="favorites-panel">
          <div v-if="favoriteStore.forumPostFavorites.length" class="post-list">
            <ForumPostCard
              v-for="post in favoriteStore.forumPostFavorites"
              :key="post.id"
              :post="post"
              @click="$router.push(`/forum/post/${post.id}`)"
            />
          </div>
          <EmptyState v-else description="暂无收藏的论坛帖子" />
          <Pagination
            v-if="favoriteStore.totalForumPostFavorites > pageSize"
            v-model:current-page="forumFavPage"
            :total="favoriteStore.totalForumPostFavorites"
            :page-size="pageSize"
          />
        </div>

        <!-- 关注分区 -->
        <div v-else-if="activeTab === 'zone-follows'" class="favorites-panel">
          <div v-if="followStore.followedZones.length" class="zone-grid">
            <Card
              v-for="zone in followStore.followedZones"
              :key="zone.id"
              class="zone-card"
            >
              <div class="zone-header">
                <h3 class="zone-name">{{ zone.zone_name }}</h3>
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
          <EmptyState v-else description="暂无关注的分区" />
          <Pagination
            v-if="followStore.totalFollowedZones > pageSize"
            v-model:current-page="zoneFollowPage"
            :total="followStore.totalFollowedZones"
            :page-size="pageSize"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useFavoriteStore } from '@/stores/favorite'
import { useFollowStore } from '@/stores/follow'
import ImageUploader from '@/components/ImageUploader.vue'
import FilterButton from '@/components/FilterButton.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import Card from '@/components/Card.vue'
import EmptyState from '@/components/EmptyState.vue'
import Pagination from '@/components/Pagination.vue'
import ForumPostCard from '@/components/ForumPostCard.vue'
import Avatar from '@/components/Avatar.vue'
import PillLink from '@/components/PillLink.vue'

const authStore = useAuthStore()
const userStore = useUserStore()
const favoriteStore = useFavoriteStore()
const followStore = useFollowStore()

const previewAvatar = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const showPassword = ref(false)

const form = reactive({
  username: '',
  email: '',
  personal_profile: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errors = reactive<Record<string, string>>({})

const activeTab = ref('profile')
const pageSize = 20
const blogFavPage = ref(1)
const forumFavPage = ref(1)
const zoneFollowPage = ref(1)

async function switchTab(key: string) {
  activeTab.value = key
  if (key === 'blog-favorites') {
    blogFavPage.value = 1
    await favoriteStore.fetchBlogPostFavorites({ skip: 0, limit: pageSize })
  } else if (key === 'forum-favorites') {
    forumFavPage.value = 1
    await favoriteStore.fetchForumPostFavorites({ skip: 0, limit: pageSize })
  } else if (key === 'zone-follows') {
    zoneFollowPage.value = 1
    await followStore.fetchFollowedZones({ skip: 0, limit: pageSize })
  }
}

watch(blogFavPage, () => {
  favoriteStore.fetchBlogPostFavorites({ skip: (blogFavPage.value - 1) * pageSize, limit: pageSize })
})

watch(forumFavPage, () => {
  favoriteStore.fetchForumPostFavorites({ skip: (forumFavPage.value - 1) * pageSize, limit: pageSize })
})

watch(zoneFollowPage, () => {
  followStore.fetchFollowedZones({ skip: (zoneFollowPage.value - 1) * pageSize, limit: pageSize })
})

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}

const permissionLabel = computed(() => {
  const p = authStore.user?.permission
  if (p === 2) return '超级管理员'
  if (p === 1) return '管理员'
  return '普通用户'
})

const permissionClass = computed(() => {
  const p = authStore.user?.permission
  if (p === 2) return 'super-admin'
  if (p === 1) return 'admin'
  return 'user'
})

onMounted(() => {
  if (authStore.user) {
    form.username = authStore.user.username
    form.email = authStore.user.email
    form.personal_profile = authStore.user.personal_profile || ''
  }
})

function handleFileSelect(file: File) {
  selectedFile.value = file
  if (previewAvatar.value) {
    URL.revokeObjectURL(previewAvatar.value)
  }
  previewAvatar.value = URL.createObjectURL(file)
}

onUnmounted(() => {
  if (previewAvatar.value) {
    URL.revokeObjectURL(previewAvatar.value)
  }
})

function togglePasswordSection() {
  showPassword.value = !showPassword.value
  if (!showPassword.value) {
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    clearFieldErrors(['oldPassword', 'newPassword', 'confirmPassword'])
  }
}

function clearFieldErrors(fields: string[]) {
  fields.forEach((f) => delete errors[f])
}

function validateProfile(): boolean {
  let valid = true
  clearFieldErrors(['username', 'email', 'personal_profile'])

  if (!form.username || form.username.length < 3 || form.username.length > 64) {
    errors.username = '用户名长度为 3-64 字符'
    valid = false
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!form.email || !emailRegex.test(form.email)) {
    errors.email = '请输入有效的邮箱地址'
    valid = false
  }

  return valid
}

function validatePassword(): boolean {
  let valid = true
  clearFieldErrors(['oldPassword', 'newPassword', 'confirmPassword'])

  if (!passwordForm.oldPassword) {
    errors.oldPassword = '请输入旧密码'
    valid = false
  } else if (passwordForm.oldPassword.length < 6 || passwordForm.oldPassword.length > 128) {
    errors.oldPassword = '旧密码长度为 6-128 字符'
    valid = false
  }

  if (!passwordForm.newPassword || passwordForm.newPassword.length < 6 || passwordForm.newPassword.length > 128) {
    errors.newPassword = '新密码长度为 6-128 字符'
    valid = false
  }

  if (passwordForm.newPassword === passwordForm.oldPassword && passwordForm.newPassword) {
    errors.newPassword = '新密码不能与旧密码相同'
    valid = false
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    errors.confirmPassword = '两次输入的密码不一致'
    valid = false
  }

  return valid
}

async function handleSave() {
  if (!authStore.user) return
  if (!validateProfile()) return

  try {
    await userStore.updateProfile(authStore.user.id, {
      username: form.username,
      email: form.email,
      personal_profile: form.personal_profile
    }, selectedFile.value || undefined)
    selectedFile.value = null
    previewAvatar.value = null
  } catch (error: any) {
    if (error.response?.status === 422 && error.response.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        detail.forEach((item: any) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field && typeof field === 'string') {
            errors[field] = item.msg
          }
        })
      }
    }
  }
}

async function handleChangePassword() {
  if (!validatePassword()) return

  try {
    await userStore.changePassword({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
  } catch (error: any) {
    const status = error.response?.status
    const message = error.response?.data?.message

    if (status === 401) {
      errors.oldPassword = message || '旧密码错误'
    } else if (status === 400) {
      errors.newPassword = message || '新密码不能与旧密码相同'
    } else if (status === 422 && error.response.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        detail.forEach((item: any) => {
          const field = item.loc?.[item.loc.length - 1]
          if (field === 'old_password') {
            errors.oldPassword = item.msg
          } else if (field === 'new_password') {
            errors.newPassword = item.msg
          }
        })
      }
    }
  }
}
</script>

<style scoped>
.profile-hero {
  height: 320px;
  background: var(--bg-black);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.profile-name {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 8px;
}
.permission-badge {
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-pill);
}
.permission-badge.user {
  background: rgba(255, 255, 255, 0.1);
  color: #8e8e93;
}
.permission-badge.admin {
  background: rgba(0, 113, 227, 0.2);
  color: var(--apple-blue);
}
.permission-badge.super-admin {
  background: rgba(175, 82, 222, 0.2);
  color: var(--admin-purple);
}
.profile-form-section {
  background: var(--bg-gray);
  padding: 60px 0;
}
.profile-form {
  max-width: 600px;
  margin: 0 auto;
}
.form-group {
  margin-bottom: 20px;
}
.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
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
  font-family: var(--font-body);
}
.form-input:focus {
  border-color: var(--apple-blue);
}
.field-error {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--error-red);
}
.password-section {
  margin-top: 40px;
}
.section-toggle {
  font-size: 14px;
  font-weight: 600;
  color: var(--link-blue);
  cursor: pointer;
  margin-bottom: 16px;
}
.password-form {
  padding-top: 8px;
}

/* ---------- Tabs ---------- */
.profile-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.profile-tab {
  padding: 6px 14px;
  font-size: 14px;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.profile-tab.active {
  color: var(--apple-blue);
  border-bottom-color: var(--apple-blue);
}

/* ---------- Favorites Panel ---------- */
.favorites-panel {
  max-width: 900px;
  margin: 0 auto;
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
}

/* Forum favorites */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

/* Zone follows */
.zone-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 32px;
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
</style>
