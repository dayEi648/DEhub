<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, VideoPlay, Headset, Microphone, User, Setting, SwitchButton, ArrowDown, House } from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import { useUserDetail } from './useUserDetail'
import { getUser, clearAuth } from '@/utils/authStorage'
import { logout } from '@/api/user'

const {
  user,
  userLoading,
  recentSongs,
  recentLoading,
  playlists,
  playlistLoading,
  songPageData,
  songPageNum,
  songPageSize,
  songTotal,
  songLoading,
  albumPageData,
  albumPageNum,
  albumPageSize,
  albumTotal,
  albumLoading,
  activeTab,
  visibleTabs,
  isFollowed,
  followLoading,
  toggleFollow,
  onMessage,
  playSong,
  goPlaylistDetail,
  goAlbumDetail,
  goBack,
  formatDate,
  genderLabel,
  loadSongs,
  loadAlbums
} = useUserDetail()

const router = useRouter()
const currentUser = computed(() => getUser())
const displayName = computed(() => currentUser.value?.name || currentUser.value?.username || '用户')
const avatarUrl = computed(() => currentUser.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (currentUser.value?.role ?? 0) >= 2)

function defaultCover() {
  return 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
}

function goHome() {
  router.push('/home')
}

function goProfile() {
  router.push('/profile')
}

function goAdmin() {
  router.push('/users')
}

async function handleLogout() {
  try {
    await logout()
  } catch {
    // 忽略网络失败
  }
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <div class="user-detail-page">
    <!-- 背景光效 -->
    <div class="detail-bg-glow" />
    <div class="detail-stars">
      <div v-for="i in 5" :key="i" class="star-dot" :class="`star-${i}`" />
    </div>

    <!-- Header -->
    <header class="detail-header">
      <div class="header-inner">
        <div class="header-left">
          <button class="back-btn" @click="goBack">
            <el-icon size="16"><ArrowLeft /></el-icon>
            <span>返回</span>
          </button>
          <div class="header-divider" />
          <h1 class="page-title">用户详情</h1>
        </div>
        <div v-if="currentUser" class="header-right">
          <NotificationBell />
          <el-dropdown trigger="click" popper-class="user-dropdown-popper">
            <div class="header-user-card">
              <el-avatar :size="36" :src="avatarUrl" class="header-user-avatar" />
              <span class="header-user-name">{{ displayName }}</span>
              <el-icon size="12" class="header-user-arrow"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown-menu">
                <div class="dropdown-header">
                  <el-avatar :size="40" :src="avatarUrl" />
                  <div class="dropdown-meta">
                    <span class="dropdown-name">{{ displayName }}</span>
                    <span class="dropdown-level">Lv.{{ currentUser.level ?? 0 }}</span>
                  </div>
                </div>
                <el-dropdown-item :icon="House" @click="goHome">回到首页</el-dropdown-item>
                <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
                <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goAdmin">管理后台</el-dropdown-item>
                <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="detail-main">
      <div v-loading="userLoading" class="detail-content">
        <!-- 用户信息头部 -->
        <div v-if="user" class="user-info-header">
          <div class="user-avatar-large">
            <img
              v-if="user.avatar"
              :src="user.avatar"
              :alt="user.name || user.username"
            />
            <div v-else class="avatar-placeholder">
              <el-icon size="64"><Headset /></el-icon>
            </div>
          </div>
          <div class="user-meta">
            <h2 class="user-name">
              {{ user.name || user.username }}
              <el-tag v-if="user.professional" type="success" size="small" class="pro-tag">
                <el-icon size="12"><Microphone /></el-icon> 认证
              </el-tag>
            </h2>
            <div class="user-subinfo">
              @{{ user.username }}
              <span class="subinfo-divider">·</span>
              {{ genderLabel(user.gender) }}
              <span class="subinfo-divider">·</span>
              Lv.{{ user.level ?? 0 }}
              <span v-if="user.city" class="subinfo-divider">·</span>
              <span v-if="user.city">{{ user.city }}</span>
            </div>
            <p class="user-description">{{ user.description || '暂无简介' }}</p>
            <div class="user-stats">
              <div class="stat-item">
                <span class="stat-value">{{ user.likeCount ?? 0 }}</span>
                <span class="stat-label">点赞</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ user.fanCount ?? 0 }}</span>
                <span class="stat-label">粉丝</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ user.followCount ?? 0 }}</span>
                <span class="stat-label">关注</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatDate(user.createTime) }}</span>
                <span class="stat-label">入驻</span>
              </div>
            </div>
            <div class="user-actions">
              <el-button
                :type="isFollowed ? 'default' : 'primary'"
                :loading="followLoading"
                @click="toggleFollow"
              >
                {{ isFollowed ? '取关' : '关注' }}
              </el-button>
              <el-button @click="onMessage">私信</el-button>
            </div>
          </div>
        </div>

        <!-- Tab 切换栏 -->
        <div v-if="user" class="tab-bar">
          <div
            v-for="tab in visibleTabs"
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </div>
        </div>

        <!-- Tab 内容 -->
        <div v-if="user" class="tab-content">
          <!-- 个人资料 -->
          <div v-show="activeTab === 'profile'" class="profile-section">
            <div class="section-block">
              <h3 class="section-title">最近听歌</h3>
              <div v-if="recentLoading" class="loading-wrap">
                <el-skeleton :rows="3" animated />
              </div>
              <div v-else-if="recentSongs.length === 0" class="empty-tip">暂无听歌记录</div>
              <div v-else class="song-mini-list">
                <div
                  v-for="(song, i) in recentSongs"
                  :key="song.id"
                  class="song-item"
                  @click="playSong(song)"
                >
                  <span class="song-index">{{ i + 1 }}</span>
                  <img class="song-cover" :src="song.coverUrl || defaultCover()" />
                  <span class="song-name">{{ song.musicName }}</span>
                  <span class="song-author">{{ song.authorNames?.join(' / ') || '-' }}</span>
                  <el-icon class="song-play-icon" size="18"><VideoPlay /></el-icon>
                </div>
              </div>
            </div>

            <div class="section-block">
              <h3 class="section-title">创建的歌单</h3>
              <div v-if="playlistLoading" class="loading-wrap">
                <el-skeleton :rows="2" animated />
              </div>
              <div v-else-if="playlists.length === 0" class="empty-tip">暂无创建的歌单</div>
              <div v-else class="playlist-grid">
                <div
                  v-for="pl in playlists"
                  :key="pl.id"
                  class="playlist-card"
                  @click="goPlaylistDetail(pl.id)"
                >
                  <img class="playlist-cover" :src="pl.imageUrl || defaultCover()" />
                  <div class="playlist-name">{{ pl.playlistName }}</div>
                  <div class="playlist-count">{{ pl.songIds?.length || 0 }}首</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 个人空间 -->
          <div v-show="activeTab === 'space'" class="space-section">
            <el-empty description="个人空间开发中..." />
          </div>

          <!-- 所有单曲 -->
          <div v-show="activeTab === 'songs'" class="songs-section">
            <el-table
              :data="songPageData"
              v-loading="songLoading"
              class="dark-table"
              style="width: 100%"
            >
              <el-table-column type="index" width="50" />
              <el-table-column label="歌曲" min-width="240">
                <template #default="{ row }">
                  <div class="song-cell">
                    <img :src="row.image1Url || defaultCover()" class="song-cell-cover" />
                    <span class="song-cell-name">{{ row.musicName }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="歌手" min-width="160">
                <template #default="{ row }">
                  {{ row.authorNameList?.join(' / ') || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="albumName" label="专辑" min-width="160" />
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button circle size="small" @click="playSong(row)">
                    <el-icon size="16"><VideoPlay /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="pagination-wrap">
              <el-pagination
                v-model:current-page="songPageNum"
                v-model:page-size="songPageSize"
                :total="songTotal"
                layout="prev, pager, next"
                @change="loadSongs"
              />
            </div>
          </div>

          <!-- 所有专辑 -->
          <div v-show="activeTab === 'albums'" class="albums-section">
            <div v-if="albumLoading" class="loading-wrap">
              <el-skeleton :rows="2" animated />
            </div>
            <div v-else-if="albumPageData.length === 0" class="empty-tip">暂无专辑</div>
            <div v-else class="album-grid">
              <div
                v-for="album in albumPageData"
                :key="album.id"
                class="album-card"
                @click="goAlbumDetail(album.id)"
              >
                <div class="album-cover-wrap">
                  <img class="album-cover" :src="album.image1Url || defaultCover()" />
                  <div class="album-mask">
                    <el-icon size="32"><VideoPlay /></el-icon>
                  </div>
                </div>
                <div class="album-name">{{ album.albumName }}</div>
                <div class="album-meta">
                  {{ album.songIds?.length || 0 }}首 · {{ album.playCount || 0 }}次播放
                </div>
              </div>
            </div>
            <div class="pagination-wrap">
              <el-pagination
                v-model:current-page="albumPageNum"
                v-model:page-size="albumPageSize"
                :total="albumTotal"
                layout="prev, pager, next"
                @change="loadAlbums"
              />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@import './user-detail.css';

/* ========== Dark Table Overrides ========== */
.dark-table {
  background: transparent;
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.06);
  --el-table-header-text-color: #94a3b8;
  --el-table-text-color: #e2e8f0;
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.03);
}

.dark-table :deep(.el-table__body-wrapper .el-table__body tr td.el-table__cell) {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04) !important;
  color: #e2e8f0;
}

.dark-table :deep(.el-table__body-wrapper .el-table__body tr:nth-child(odd) td.el-table__cell) {
  background: rgba(255, 255, 255, 0.015) !important;
}

.dark-table :deep(.el-table__body-wrapper .el-table__body tr:nth-child(even) td.el-table__cell) {
  background: rgba(255, 255, 255, 0.035) !important;
}

.dark-table :deep(.el-table__body-wrapper .el-table__body tr:hover td.el-table__cell) {
  background: rgba(107, 70, 193, 0.15) !important;
}

.dark-table :deep(.el-table__header-wrapper .el-table__header th.el-table__cell) {
  background: rgba(255, 255, 255, 0.06) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  color: #94a3b8 !important;
  font-weight: 500;
}

.dark-table :deep(.el-table__empty-text) {
  color: #64748b;
}

.dark-table :deep(.el-button--small) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
}

.dark-table :deep(.el-button--small:hover) {
  background: rgba(107, 70, 193, 0.2);
  border-color: rgba(139, 92, 246, 0.3);
  color: #ffffff;
}
</style>
