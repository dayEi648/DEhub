<script setup lang="ts">
import { onMounted } from 'vue'
import {
  ChatDotRound,
  Delete,
  EditPen,
  MoreFilled,
  Picture,
  Plus,
  Share,
  UserFilled
} from '@element-plus/icons-vue'
import { useProfileSpace } from './useProfileSpace'
import CommentSection from '@/components/CommentSection/CommentSection.vue'
import type { SpacePostVO } from '@/types/spacePost'
import type { UserVO } from '@/types/user'

const {
  currentUser,
  posts,
  total,
  pageNum,
  pageSize,
  loading,
  stats,
  showPublishArea,
  publishContent,
  publishImages,
  isPublishing,
  imageUploading,
  showForwardDialog,
  forwardTarget,
  forwardContent,
  isForwarding,
  activeCommentPostId,
  showMentionDialog,
  mentionKeyword,
  mentionLoading,
  mentionUsers,
  loadPosts,
  loadStats,
  publishPost,
  toggleLike,
  openForward,
  submitForward,
  removePost,
  uploadImageAction,
  removeImage,
  searchMentionUsers,
  addMention,
  formatTime,
  handlePageChange
} = useProfileSpace()

const avatarUrl = currentUser.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
const displayName = currentUser.value?.name || currentUser.value?.username || '用户'
const userLevel = currentUser.value?.level || 1
const fanCount = currentUser.value?.fanIds?.length || 0
const followCount = currentUser.value?.followIds?.length || 0

function onImageSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    uploadImageAction(input.files[0])
    input.value = ''
  }
}

function onOpenMention() {
  showMentionDialog.value = true
  mentionKeyword.value = ''
  mentionUsers.value = []
}

function isSelfPost(post: SpacePostVO) {
  return post.userId === currentUser.value?.id
}

onMounted(() => {
  loadPosts(true)
  loadStats()
})
</script>

<template>
  <div class="space-page">
    <!-- 顶部用户信息卡片 -->
    <div class="space-header-card">
      <div class="space-header-left">
        <el-avatar :size="80" :src="avatarUrl" class="space-header-avatar" />
        <div class="space-header-info">
          <div class="space-header-name">{{ displayName }}</div>
          <div class="space-header-level">Lv.{{ userLevel }}</div>
        </div>
      </div>
      <div class="space-header-stats">
        <div class="stat-item">
          <div class="stat-value">{{ stats.postCount }}</div>
          <div class="stat-label">说说</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.likeCount }}</div>
          <div class="stat-label">获赞</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ fanCount }}</div>
          <div class="stat-label">粉丝</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ followCount }}</div>
          <div class="stat-label">关注</div>
        </div>
      </div>
    </div>

    <!-- 发表区 -->
    <div class="publish-section">
      <div v-if="!showPublishArea" class="publish-trigger" @click="showPublishArea = true">
        <el-avatar :size="40" :src="avatarUrl" />
        <div class="publish-trigger-text">分享你的音乐心情...</div>
        <el-button type="primary" :icon="EditPen" round>写说说</el-button>
      </div>

      <div v-else class="publish-form">
        <el-input
          v-model="publishContent"
          type="textarea"
          :rows="4"
          placeholder="分享你的音乐心情..."
          maxlength="500"
          show-word-limit
          resize="none"
          class="publish-input"
        />

        <!-- 图片预览 -->
        <div v-if="publishImages.length > 0" class="publish-image-preview">
          <div v-for="(img, idx) in publishImages" :key="idx" class="preview-img-wrap">
            <img :src="img" class="preview-img" />
            <button class="preview-img-remove" @click="removeImage(idx)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
          <label v-if="publishImages.length < 9" class="preview-img-add">
            <el-icon><Plus /></el-icon>
            <input type="file" accept="image/*" hidden @change="onImageSelect" />
          </label>
        </div>

        <!-- 工具栏 -->
        <div class="publish-toolbar">
          <div class="toolbar-left">
            <label v-if="publishImages.length < 9" class="toolbar-btn" title="添加图片">
              <el-icon><Picture /></el-icon>
              <span>图片</span>
              <input type="file" accept="image/*" hidden @change="onImageSelect" />
            </label>
            <button class="toolbar-btn" title="@提及" @click="onOpenMention">
              <el-icon><UserFilled /></el-icon>
              <span>@TA</span>
            </button>
          </div>
          <div class="toolbar-right">
            <el-button @click="showPublishArea = false">取消</el-button>
            <el-button
              type="primary"
              :loading="isPublishing || imageUploading"
              @click="publishPost"
            >
              发表
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 说说列表 -->
    <div v-loading="loading" class="post-list">
      <div v-if="posts.length === 0" class="empty-state">
        <el-icon :size="48" class="empty-icon"><ChatDotRound /></el-icon>
        <p>还没有说说，快来发表第一条吧~</p>
      </div>

      <div
        v-for="post in posts"
        :key="post.id"
        class="post-card"
      >
        <!-- 头部 -->
        <div class="post-header">
          <el-avatar :size="48" :src="post.userAvatar || avatarUrl" />
          <div class="post-meta">
            <div class="post-username">{{ post.userName || displayName }}</div>
            <div class="post-time">{{ formatTime(post.createTime) }}</div>
          </div>
          <el-dropdown v-if="isSelfPost(post)" trigger="click">
            <button class="post-more-btn">
              <el-icon><MoreFilled /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :icon="Delete" @click="removePost(post)">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <!-- 内容 -->
        <div class="post-content">
          <div class="post-text">{{ post.content }}</div>

          <!-- 图片网格 -->
          <div v-if="post.images && post.images.length > 0" class="post-image-grid" :class="`grid-${Math.min(post.images.length, 9)}`">
            <div
              v-for="(img, idx) in post.images.slice(0, 9)"
              :key="idx"
              class="post-image-item"
            >
              <img :src="img" />
            </div>
          </div>
        </div>

        <!-- 转发卡片 -->
        <div v-if="post.postType === 'forward' && post.sourceContent" class="forward-card">
          <div class="forward-header">
            <el-avatar :size="24" :src="post.sourceUserAvatar || avatarUrl" />
            <span class="forward-name">{{ post.sourceUserName || '未知用户' }}</span>
          </div>
          <div class="forward-text">{{ post.sourceContent }}</div>
          <div v-if="post.sourceImages && post.sourceImages.length > 0" class="forward-images">
            <img
              v-for="(img, idx) in post.sourceImages.slice(0, 3)"
              :key="idx"
              :src="img"
              class="forward-img"
            />
          </div>
        </div>

        <!-- 操作栏 -->
        <div class="post-actions">
          <button
            class="action-btn"
            :class="{ active: post.liked }"
            @click="toggleLike(post)"
          >
            <svg class="action-icon" :class="{ active: post.liked }" viewBox="0 0 24 24" width="16" height="16">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>{{ post.likeCount || 0 }}</span>
          </button>
          <button
            class="action-btn"
            :class="{ active: activeCommentPostId === post.id }"
            @click="activeCommentPostId = activeCommentPostId === post.id ? null : post.id"
          >
            <el-icon><ChatDotRound /></el-icon>
            <span>{{ post.commentCount || 0 }}</span>
          </button>
          <button class="action-btn" @click="openForward(post)">
            <el-icon><Share /></el-icon>
            <span>{{ post.forwardCount || 0 }}</span>
          </button>
        </div>

        <!-- 评论区 -->
        <div v-if="activeCommentPostId === post.id" class="post-comment-section">
          <CommentSection scene-type="space" :scene-id="post.id" />
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pagination-wrap">
        <el-pagination
          v-model:current-page="pageNum"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @change="handlePageChange"
        />
      </div>
    </div>

    <!-- 转发对话框 -->
    <el-dialog
      v-model="showForwardDialog"
      title="转发到空间"
      width="500px"
      class="space-dialog"
      :close-on-click-modal="false"
    >
      <div class="forward-preview" v-if="forwardTarget">
        <div class="forward-preview-header">
          <el-avatar :size="32" :src="forwardTarget.userAvatar || avatarUrl" />
          <span>{{ forwardTarget.userName || '未知用户' }}</span>
        </div>
        <div class="forward-preview-text">{{ forwardTarget.content }}</div>
      </div>
      <el-input
        v-model="forwardContent"
        type="textarea"
        :rows="3"
        placeholder="说点什么..."
        maxlength="500"
        show-word-limit
        resize="none"
        class="forward-input"
      />
      <template #footer>
        <el-button @click="showForwardDialog = false">取消</el-button>
        <el-button type="primary" :loading="isForwarding" @click="submitForward">
          转发
        </el-button>
      </template>
    </el-dialog>

    <!-- @提及对话框 -->
    <el-dialog
      v-model="showMentionDialog"
      title="@提及用户"
      width="400px"
      class="space-dialog"
    >
      <el-input
        v-model="mentionKeyword"
        placeholder="搜索用户昵称..."
        clearable
        @keyup.enter="searchMentionUsers"
      >
        <template #append>
          <el-button :loading="mentionLoading" @click="searchMentionUsers">搜索</el-button>
        </template>
      </el-input>
      <div v-loading="mentionLoading" class="mention-user-list">
        <div
          v-for="user in mentionUsers"
          :key="user.id"
          class="mention-user-item"
          @click="addMention(user as UserVO)"
        >
          <el-avatar :size="36" :src="user.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'" />
          <span class="mention-user-name">{{ user.name || user.username }}</span>
        </div>
        <div v-if="mentionUsers.length === 0 && !mentionLoading" class="mention-empty">
          输入昵称后点击搜索
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
/* 页面容器 */
.space-page {
  padding: 24px;
  max-width: 720px;
  margin: 0 auto;
}

/* 顶部用户卡片 */
.space-header-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 20px;
}

.space-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.space-header-avatar {
  border: 3px solid rgba(107, 70, 193, 0.4);
  box-shadow: 0 0 24px rgba(107, 70, 193, 0.2);
}

.space-header-name {
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}

.space-header-level {
  font-size: 12px;
  color: #a78bfa;
  background: rgba(107, 70, 193, 0.12);
  padding: 2px 10px;
  border-radius: 10px;
  display: inline-block;
  margin-top: 4px;
}

.space-header-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

/* 发表区 */
.publish-section {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 20px;
  overflow: hidden;
}

.publish-trigger {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: background 0.3s;
}

.publish-trigger:hover {
  background: rgba(255, 255, 255, 0.02);
}

.publish-trigger-text {
  flex: 1;
  color: #64748b;
  font-size: 14px;
}

.publish-form {
  padding: 20px;
}

.publish-input :deep(.el-textarea__inner) {
  background: rgba(10, 6, 20, 0.4);
  border-color: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.publish-input :deep(.el-input__count) {
  background: transparent;
  color: #64748b;
}

/* 图片预览 */
.publish-image-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.preview-img-wrap {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 8px;
  overflow: hidden;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-img-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.preview-img-add {
  width: 100px;
  height: 100px;
  border-radius: 8px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #64748b;
  cursor: pointer;
  transition: all 0.3s;
}

.preview-img-add:hover {
  border-color: rgba(107, 70, 193, 0.4);
  color: #a78bfa;
}

/* 工具栏 */
.publish-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.toolbar-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

/* 说说列表 */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 20px;
  transition: all 0.3s ease;
}

.post-card:hover {
  border-color: rgba(107, 70, 193, 0.12);
}

/* 头部 */
.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.post-meta {
  flex: 1;
}

.post-username {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
}

.post-time {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.post-more-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.post-more-btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}

/* 内容 */
.post-content {
  margin-bottom: 12px;
}

.post-text {
  font-size: 14px;
  line-height: 1.7;
  color: #cbd5e1;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 图片网格 */
.post-image-grid {
  display: grid;
  gap: 6px;
  margin-top: 12px;
}

.post-image-grid.grid-1 {
  grid-template-columns: 1fr;
  max-width: 400px;
}

.post-image-grid.grid-1 .post-image-item {
  aspect-ratio: auto;
}

.post-image-grid.grid-1 .post-image-item img {
  width: 100%;
  height: auto;
  object-fit: contain;
  border-radius: 8px;
}

.post-image-grid.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.post-image-grid.grid-3,
.post-image-grid.grid-5,
.post-image-grid.grid-6,
.post-image-grid.grid-9 {
  grid-template-columns: repeat(3, 1fr);
}

.post-image-grid.grid-4 {
  grid-template-columns: repeat(2, 1fr);
}

.post-image-grid.grid-7,
.post-image-grid.grid-8 {
  grid-template-columns: repeat(3, 1fr);
}

.post-image-item {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.post-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.post-image-item:hover img {
  transform: scale(1.03);
}

/* 转发卡片 */
.forward-card {
  background: rgba(10, 6, 20, 0.4);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.forward-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.forward-name {
  font-size: 13px;
  font-weight: 600;
  color: #94a3b8;
}

.forward-text {
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.6;
  white-space: pre-wrap;
}

.forward-images {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.forward-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 6px;
}

/* 操作栏 */
.post-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
  justify-content: center;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #e2e8f0;
}

.action-btn.active {
  color: #ec4899;
}

.action-icon {
  transition: all 0.3s;
}

.action-icon.active {
  fill: #ec4899;
}

/* 评论区 */
.post-comment-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #64748b;
  gap: 12px;
}

.empty-icon {
  color: #475569;
  opacity: 0.5;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: #c4b5fd;
  --el-pagination-button-color: #94a3b8;
  --el-pagination-button-disabled-color: #475569;
}

/* 转发预览 */
.forward-preview {
  background: rgba(10, 6, 20, 0.4);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.forward-preview-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #94a3b8;
}

.forward-preview-text {
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* 提及用户列表 */
.mention-user-list {
  margin-top: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.mention-user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.mention-user-item:hover {
  background: rgba(107, 70, 193, 0.1);
}

.mention-user-name {
  font-size: 14px;
  color: #e2e8f0;
}

.mention-empty {
  text-align: center;
  padding: 24px;
  color: #64748b;
  font-size: 13px;
}
</style>

<style>
/* Element Plus Dialog 全局样式覆盖（teleport 到 body） */
.space-dialog .el-dialog {
  background: rgba(15, 23, 42, 0.95) !important;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

.space-dialog .el-dialog__title {
  color: #e2e8f0;
}

.space-dialog .el-dialog__body {
  color: #cbd5e1;
}

.space-dialog .el-input__wrapper {
  background: rgba(10, 6, 20, 0.4);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
}

.space-dialog .el-input__inner {
  color: #e2e8f0;
}

.space-dialog .el-textarea__inner {
  background: rgba(10, 6, 20, 0.4);
  border-color: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}
</style>
