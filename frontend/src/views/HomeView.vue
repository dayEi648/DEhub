<template>
  <div class="home-page">
    <!-- Section 1: Personal Hero -->
    <section class="hero-section">
      <div class="container hero-content">
        <Avatar
          :src="authStore.user?.avatar_url"
          :name="authStore.user?.username || ''"
          :size="120"
          class="hero-avatar"
        />
        <h1 class="hero-title">Welcome back, {{ authStore.user?.username }}</h1>
        <p class="hero-bio">{{ authStore.user?.personal_profile || 'A developer exploring the world of code.' }}</p>
        <div class="hero-actions">
          <GhostButton @click="$router.push('/profile')">个人中心</GhostButton>
          <PrimaryButton @click="$router.push('/chat')">开始对话</PrimaryButton>
        </div>
      </div>
    </section>

    <!-- Section 2: Latest Articles -->
    <section class="articles-section">
      <div class="container">
        <h2 class="section-title">最新文章</h2>
        <div class="article-grid">
          <Card
            v-for="post in blogStore.posts.slice(0, 6)"
            :key="post.id"
            class="article-card"
            @click="$router.push(`/blog/${post.slug}`)"
          >
            <img v-if="post.cover_image_url" :src="post.cover_image_url" class="article-cover" />
            <div class="article-body">
              <h3 class="article-title">{{ post.title }}</h3>
              <p class="article-summary">{{ post.summary || '暂无摘要' }}</p>
              <span class="article-date">{{ formatDate(post.created_at) }}</span>
            </div>
          </Card>
        </div>
        <EmptyState
          v-if="blogStore.posts.length === 0"
          description="还没有文章"
          action-text="去博客看看"
          action-to="/blog"
        />
        <div class="section-footer">
          <PillLink to="/blog">查看全部文章 →</PillLink>
        </div>
      </div>
    </section>

    <!-- Section 3: Quick Links -->
    <section class="quick-section">
      <div class="container">
        <h2 class="section-title light">探索更多</h2>
        <div class="quick-grid">
          <Card dark class="quick-card" @click="$router.push('/forum')">
            <div class="quick-icon">💬</div>
            <h3 class="quick-name">论坛</h3>
            <p class="quick-desc">加入技术讨论</p>
          </Card>
          <Card dark class="quick-card" @click="$router.push('/chat')">
            <div class="quick-icon">🤖</div>
            <h3 class="quick-name">AI 对话</h3>
            <p class="quick-desc">与智能助手交流</p>
          </Card>
          <Card dark class="quick-card" @click="$router.push('/links')">
            <div class="quick-icon">🔗</div>
            <h3 class="quick-name">子网站</h3>
            <p class="quick-desc">探索更多项目</p>
          </Card>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blog'
import Avatar from '@/components/Avatar.vue'
import PrimaryButton from '@/components/PrimaryButton.vue'
import GhostButton from '@/components/GhostButton.vue'
import Card from '@/components/Card.vue'
import PillLink from '@/components/PillLink.vue'
import EmptyState from '@/components/EmptyState.vue'

const authStore = useAuthStore()
const blogStore = useBlogStore()

onMounted(() => {
  blogStore.fetchPosts({ limit: 6 })
})

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.hero-section {
  min-height: calc(100vh - 48px);
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
  padding: 80px 24px;
}
.hero-avatar {
  margin-bottom: 24px;
}
.hero-title {
  font-family: var(--font-display);
  font-size: 40px;
  font-weight: 600;
  line-height: 1.1;
  color: var(--text-white);
  margin-bottom: 12px;
}
.hero-bio {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.8);
  max-width: 480px;
  margin-bottom: 32px;
  line-height: 1.47;
}
.hero-actions {
  display: flex;
  gap: 16px;
}

.articles-section {
  background: var(--bg-gray);
  padding: 80px 0;
}
.section-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 400;
  line-height: 1.14;
  color: var(--text-primary);
  margin-bottom: 32px;
}
.section-title.light {
  color: var(--text-white);
}
.article-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}
.article-card {
  cursor: pointer;
  transition: transform 0.2s;
}
.article-card:hover {
  transform: translateY(-2px);
}
.article-cover {
  width: 100%;
  aspect-ratio: 16 / 10;
  object-fit: cover;
}
.article-body {
  padding: 20px;
}
.article-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.article-summary {
  font-size: 14px;
  color: var(--text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
}
.article-date {
  font-size: 12px;
  color: var(--text-tertiary);
}
.section-footer {
  text-align: right;
}

.quick-section {
  background: var(--bg-black);
  padding: 80px 0;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}
.quick-card {
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}
.quick-card:hover {
  transform: translateY(-4px);
}
.quick-icon {
  font-size: 40px;
  margin-bottom: 16px;
}
.quick-name {
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 600;
  color: var(--text-white);
  margin-bottom: 8px;
}
.quick-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}
</style>
