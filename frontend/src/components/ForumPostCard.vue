<template>
  <Card class="forum-post-card" @click="$emit('click')">
    <Avatar :size="40" :src="post.user.avatar_url" :name="post.user.username" />
    <div class="post-info">
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
</template>

<script setup lang="ts">
import type { ForumPostResponse } from '@/types'
import Card from './Card.vue'
import Avatar from './Avatar.vue'

interface Props {
  post: ForumPostResponse
}
defineProps<Props>()
defineEmits<{
  click: []
}>()

function formatDate(date: string) {
  return new Date(date).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.forum-post-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  cursor: pointer;
}
.post-info {
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
