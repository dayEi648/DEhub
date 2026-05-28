<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import {
  Search, CaretRight, Star, Headset, Grid, UserFilled, Microphone, Collection, FolderOpened,
  ArrowDown, User, Setting, SwitchButton, House
} from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import { useSearchPage } from './useSearchPage'
import type { MusicVO } from '@/types/music'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { UserVO } from '@/types/user'
import { ElMessage } from 'element-plus'
import { getUser, clearAuth } from '@/utils/authStorage'
import { logout as logoutApi } from '@/api/user'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'

const {
  keyword,
  activeTab,
  loading,
  allData,
  musicState,
  playlistState,
  albumState,
  singerState,
  userState,
  switchTab,
  doSearch,
  handlePageChange,
  goUserDetail
} = useSearchPage()

const tabs = [
  { key: 'all', label: '综合' },
  { key: 'musics', label: '单曲' },
  { key: 'playlists', label: '歌单' },
  { key: 'albums', label: '专辑' },
  { key: 'singers', label: '歌手' },
  { key: 'users', label: '用户' }
] as const

const addDialogVisible = ref(false)
const addDialogMusicId = ref(0)

function openAddToPlaylistDialog(musicId: number) {
  addDialogMusicId.value = musicId
  addDialogVisible.value = true
}

const playerStore = usePlayerStore()

function onPlay(item: MusicVO) {
  // 同步到播放器并播放
  const ok = playerStore.playTrack({
    id: item.id,
    name: item.musicName,
    artist: joinNames(item.authorNameList),
    coverUrl: item.image1Url || '',
    fileUrl: item.fileUrl || '',
    duration: 0,
    currentTime: 0,
    vip: item.vip
  }, true)
  if (!ok) return
  playerStore.showBar()
  // 跳转到播放页
  router.push(`/music/${item.id}`)
}

function defaultCover() {
  return 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
}

function joinNames(names?: string[]) {
  return names?.filter(Boolean).join(' / ') || '未知作者'
}

function formatCount(n?: number) {
  if (n == null) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function formatPlayCommentCount(n?: number) {
  if (n == null || n <= 0) return '0'
  if (n <= 999) return String(n)
  if (n <= 9999) return '999+'
  if (n >= 1000000) return '99w+'
  return Math.floor(n / 10000) + 'w+'
}

// ===== 用户下拉菜单 =====
const router = useRouter()
const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (user.value?.role ?? 0) >= 2)

function goHome() {
  router.push('/home')
}

function goProfile() {
  router.push('/profile')
}

function goAdmin() {
  router.push('/admin')
}

function goPlaylistDetail(id: number) {
  router.push(`/playlist/${id}`)
}

function goAlbumDetail(id: number) {
  router.push(`/album/${id}`)
}

async function handleLogout() {
  try {
    await logoutApi()
  } catch {
    /* 网络失败仍清除本地登录态 */
  }
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<template>
  <div class="search-page">
    <!-- 背景光晕层 -->
    <div class="search-bg-layers" aria-hidden="true"></div>

    <!-- 顶部搜索栏 -->
    <div class="search-header">
      <div class="search-header-main">
        <!-- 左侧返回首页 -->
        <div class="search-header-left">
          <a class="brand-link" @click="goHome">
            <span class="brand-logo-mini">E</span>
            <span class="brand-text-mini">EchoMemory</span>
          </a>
        </div>

        <!-- 中间搜索+Tab -->
        <div class="search-header-center">
          <div class="search-input-wrap">
            <el-input
              v-model="keyword"
              placeholder="搜索音乐、歌单、专辑、歌手..."
              class="search-input"
              size="large"
              clearable
              @keyup.enter="doSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <template #append>
                <el-button type="primary" @click="doSearch">
                  搜索
                </el-button>
              </template>
            </el-input>
          </div>

          <!-- Tab 导航 -->
          <div class="search-tabs">
            <div
              v-for="tab in tabs"
              :key="tab.key"
              class="tab-item"
              :class="{ active: activeTab === tab.key }"
              @click="switchTab(tab.key)"
            >
              {{ tab.label }}
            </div>
          </div>
        </div>

        <!-- 右侧用户菜单 -->
        <div class="search-header-right">
          <NotificationBell />
          <el-dropdown trigger="click" popper-class="user-dropdown-popper">
            <div class="user-card-mini">
              <el-avatar :size="34" :src="avatarUrl" class="user-avatar-mini" />
              <span class="user-name-mini">{{ displayName }}</span>
              <el-icon class="dropdown-arrow-mini"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-dropdown-menu">
                <div class="dropdown-header">
                  <el-avatar :size="48" :src="avatarUrl" />
                  <div class="dropdown-meta">
                    <div class="dropdown-name">{{ displayName }}</div>
                    <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                  </div>
                </div>
                <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
                <el-dropdown-item :icon="House" @click="goHome">返回首页</el-dropdown-item>
                <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goAdmin">管理后台</el-dropdown-item>
                <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="search-loading">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 综合页 -->
    <div v-else-if="activeTab === 'all'" class="search-body">
      <!-- 单曲 -->
      <section v-if="allData.musics.length > 0" class="result-section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Headset /></el-icon> 单曲
          </h3>
          <a class="section-more" @click="switchTab('musics')">
            查看更多 <el-icon><CaretRight /></el-icon>
          </a>
        </div>
        <div class="music-grid">
          <div
            v-for="song in allData.musics"
            :key="song.id"
            class="music-row-card"
            @click="onPlay(song)"
          >
            <div class="music-row-cover">
              <img v-if="song.image1Url" :src="song.image1Url" :alt="song.musicName" />
              <div v-else class="cover-placeholder">
                <el-icon><Headset /></el-icon>
              </div>
              <div class="music-play-overlay">
                <el-icon><CaretRight /></el-icon>
              </div>
            </div>
            <div class="music-row-info">
              <div class="music-row-name" :title="song.musicName">{{ song.musicName }}</div>
              <div class="music-row-artist">{{ joinNames(song.authorNameList) }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- 歌单 -->
      <section v-if="allData.playlists.length > 0" class="result-section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Collection /></el-icon> 歌单
          </h3>
          <a class="section-more" @click="switchTab('playlists')">
            查看更多 <el-icon><CaretRight /></el-icon>
          </a>
        </div>
        <div class="card-grid">
          <div
            v-for="pl in allData.playlists"
            :key="pl.id"
            class="media-card playlist-card"
            @click="goPlaylistDetail(pl.id)"
          >
            <div class="media-cover">
              <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
              <div v-else class="cover-placeholder">
                <el-icon><Collection /></el-icon>
              </div>
            </div>
            <div class="media-name" :title="pl.playlistName">{{ pl.playlistName }}</div>
            <div class="media-meta">
              {{ pl.songIds?.length || 0 }}首 · 收藏{{ formatCount(pl.collectCount) }}
            </div>
          </div>
        </div>
      </section>

      <!-- 专辑 -->
      <section v-if="allData.albums.length > 0" class="result-section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><FolderOpened /></el-icon> 专辑
          </h3>
          <a class="section-more" @click="switchTab('albums')">
            查看更多 <el-icon><CaretRight /></el-icon>
          </a>
        </div>
        <div class="card-grid">
          <div
            v-for="al in allData.albums"
            :key="al.id"
            class="media-card album-card"
            @click="goAlbumDetail(al.id)"
          >
            <div class="media-cover">
              <img v-if="al.image1Url" :src="al.image1Url" :alt="al.albumName" />
              <div v-else class="cover-placeholder">
                <el-icon><FolderOpened /></el-icon>
              </div>
            </div>
            <div class="media-name" :title="al.albumName">{{ al.albumName }}</div>
            <div class="media-meta">
              {{ joinNames(al.authorNames) }} · 收藏{{ formatCount(al.collectCount) }}
            </div>
          </div>
        </div>
      </section>

      <!-- 歌手 -->
      <section v-if="allData.singers.length > 0" class="result-section">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Microphone /></el-icon> 歌手
          </h3>
          <a class="section-more" @click="switchTab('singers')">
            查看更多 <el-icon><CaretRight /></el-icon>
          </a>
        </div>
        <div class="card-grid user-grid">
          <div
            v-for="singer in allData.singers"
            :key="singer.id"
            class="user-card"
            @click="goUserDetail(singer.id)"
          >
            <div class="user-avatar">
              <img v-if="singer.avatar" :src="singer.avatar" :alt="singer.name || singer.username" />
              <div v-else class="avatar-placeholder">
                <el-icon><UserFilled /></el-icon>
              </div>
            </div>
            <div class="user-name">{{ singer.name || singer.username }}</div>
            <div class="user-meta">{{ singer.songCount || 0 }}首单曲</div>
          </div>
        </div>
      </section>

      <!-- 无结果 -->
      <div v-if="!allData.musics.length && !allData.playlists.length && !allData.albums.length && !allData.singers.length" class="empty-state">
        <el-icon :size="48"><Search /></el-icon>
        <p>未找到与 "{{ keyword }}" 相关的内容</p>
      </div>
    </div>

    <!-- 单曲页 -->
    <div v-else-if="activeTab === 'musics'" class="search-body">
      <el-table :data="musicState.records" class="music-table" v-loading="loading">
        <el-table-column label="歌曲" min-width="280">
          <template #default="{ row }: { row: MusicVO }">
            <div class="table-song">
              <div class="table-cover">
                <img v-if="row.image1Url" :src="row.image1Url" />
                <div v-else class="cover-placeholder small"><el-icon><Headset /></el-icon></div>
              </div>
              <div class="table-song-info">
                <div class="table-song-name">{{ row.musicName }}</div>
                <div class="table-song-artist">{{ joinNames(row.authorNameList) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="专辑" prop="albumName" min-width="160" />
        <el-table-column label="播放" min-width="100">
          <template #default="{ row }: { row: MusicVO }">
            {{ formatPlayCommentCount(row.playCount) }}
          </template>
        </el-table-column>
        <el-table-column label="评论" min-width="100">
          <template #default="{ row }: { row: MusicVO }">
            {{ formatPlayCommentCount(row.commentCount) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }: { row: MusicVO }">
            <el-button circle size="small" @click.stop="onPlay(row)">
              <el-icon><CaretRight /></el-icon>
            </el-button>
            <el-button circle size="small" @click="openAddToPlaylistDialog(row.id)">
              <el-icon><Star /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="musicState.pageNum"
          :page-size="musicState.pageSize"
          :total="musicState.total"
          layout="prev, pager, next"
          @change="handlePageChange('musics', $event)"
        />
      </div>
    </div>

    <!-- 歌单页 -->
    <div v-else-if="activeTab === 'playlists'" class="search-body">
      <div class="card-grid full-grid">
        <div
          v-for="pl in playlistState.records"
          :key="pl.id"
          class="media-card playlist-card large"
          @click="goPlaylistDetail(pl.id)"
        >
          <div class="media-cover large">
            <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
            <div v-else class="cover-placeholder"><el-icon><Collection /></el-icon></div>
          </div>
          <div class="media-name" :title="pl.playlistName">{{ pl.playlistName }}</div>
          <div class="media-meta">
            {{ pl.songIds?.length || 0 }}首 · 收藏{{ formatCount(pl.collectCount) }}
          </div>
        </div>
      </div>
      <div v-if="!playlistState.records.length && !loading" class="empty-state">
        <p>未找到相关歌单</p>
      </div>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="playlistState.pageNum"
          :page-size="playlistState.pageSize"
          :total="playlistState.total"
          layout="prev, pager, next"
          @change="handlePageChange('playlists', $event)"
        />
      </div>
    </div>

    <!-- 专辑页 -->
    <div v-else-if="activeTab === 'albums'" class="search-body">
      <div class="card-grid full-grid">
        <div
          v-for="al in albumState.records"
          :key="al.id"
          class="media-card album-card large"
          @click="goAlbumDetail(al.id)"
        >
          <div class="media-cover large">
            <img v-if="al.image1Url" :src="al.image1Url" :alt="al.albumName" />
            <div v-else class="cover-placeholder"><el-icon><FolderOpened /></el-icon></div>
          </div>
          <div class="media-name" :title="al.albumName">{{ al.albumName }}</div>
          <div class="media-meta">
            {{ joinNames(al.authorNames) }} · 收藏{{ formatCount(al.collectCount) }}
          </div>
          <div class="media-meta" v-if="al.createTime">
            {{ al.createTime.split('T')[0] }}
          </div>
        </div>
      </div>
      <div v-if="!albumState.records.length && !loading" class="empty-state">
        <p>未找到相关专辑</p>
      </div>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="albumState.pageNum"
          :page-size="albumState.pageSize"
          :total="albumState.total"
          layout="prev, pager, next"
          @change="handlePageChange('albums', $event)"
        />
      </div>
    </div>

    <!-- 歌手页 -->
    <div v-else-if="activeTab === 'singers'" class="search-body">
      <div class="card-grid user-grid full-grid">
        <div
          v-for="singer in singerState.records"
          :key="singer.id"
          class="user-card large"
          @click="goUserDetail(singer.id)"
        >
          <div class="user-avatar large">
            <img v-if="singer.avatar" :src="singer.avatar" :alt="singer.name || singer.username" />
            <div v-else class="avatar-placeholder"><el-icon><UserFilled /></el-icon></div>
          </div>
          <div class="user-name">{{ singer.name || singer.username }}</div>
          <div class="user-meta">{{ singer.songCount || 0 }}首单曲</div>
        </div>
      </div>
      <div v-if="!singerState.records.length && !loading" class="empty-state">
        <p>未找到相关歌手</p>
      </div>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="singerState.pageNum"
          :page-size="singerState.pageSize"
          :total="singerState.total"
          layout="prev, pager, next"
          @change="handlePageChange('singers', $event)"
        />
      </div>
    </div>

    <!-- 用户页 -->
    <div v-else-if="activeTab === 'users'" class="search-body">
      <div class="card-grid user-grid full-grid">
        <div
          v-for="user in userState.records"
          :key="user.id"
          class="user-card large"
          @click="goUserDetail(user.id)"
        >
          <div class="user-avatar large">
            <img v-if="user.avatar" :src="user.avatar" :alt="user.name || user.username" />
            <div v-else class="avatar-placeholder"><el-icon><UserFilled /></el-icon></div>
          </div>
          <div class="user-name">{{ user.name || user.username }}</div>
        </div>
      </div>
      <div v-if="!userState.records.length && !loading" class="empty-state">
        <p>未找到相关用户</p>
      </div>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="userState.pageNum"
          :page-size="userState.pageSize"
          :total="userState.total"
          layout="prev, pager, next"
          @change="handlePageChange('users', $event)"
        />
      </div>
    </div>

    <AddToPlaylistDialog
      :visible="addDialogVisible"
      :music-id="addDialogMusicId"
      @submit="addDialogVisible = false"
      @cancel="addDialogVisible = false"
    />
  </div>
</template>

<style scoped src="./search.css"></style>

<style scoped>
/* 分页样式（含 :deep 需放在内联 scoped style 中） */
.pagination-wrap :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-hover-color: #a78bfa;
  --el-pagination-text-color: rgba(255, 255, 255, 0.6);
  --el-pagination-button-disabled-color: rgba(255, 255, 255, 0.3);
}

.pagination-wrap :deep(.el-pagination button) {
  background: transparent;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  min-width: 32px;
  height: 32px;
}

.pagination-wrap :deep(.el-pagination button:not(:disabled):hover) {
  color: #a78bfa;
  border-color: rgba(167, 139, 250, 0.3);
  background: rgba(107, 70, 193, 0.1);
}

.pagination-wrap :deep(.el-pagination button:disabled) {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.04);
}

.pagination-wrap :deep(.el-pager li) {
  background: transparent;
  border-radius: 8px;
  border: 1px solid transparent;
  min-width: 32px;
  height: 32px;
  line-height: 30px;
  font-size: 13px;
  margin: 0 4px;
  padding: 0;
}

.pagination-wrap :deep(.el-pager li:not(.is-active):hover) {
  color: #a78bfa;
  background: rgba(107, 70, 193, 0.12);
  border-color: rgba(167, 139, 250, 0.15);
}

.pagination-wrap :deep(.el-pager li.is-active) {
  background: #6b46c1;
  color: white;
  border-color: transparent;
  box-shadow: 0 2px 8px rgba(107, 70, 193, 0.4);
}
</style>

<style>
/* 下拉菜单全局样式（搜索页独立加载时需要） */
.user-dropdown-popper {
  --el-dropdown-menuItem-hover-fill: rgba(107, 70, 193, 0.15);
  --el-dropdown-menuItem-hover-color: #e2e8f0;
}

.user-dropdown-menu {
  background: #272729 !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.user-dropdown-menu .dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.user-dropdown-menu .dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-dropdown-menu .dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.user-dropdown-menu .dropdown-level {
  font-size: 12px;
  color: #a78bfa;
  font-weight: 500;
}

.user-dropdown-menu .el-dropdown-menu__item {
  color: rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.user-dropdown-menu .el-dropdown-menu__item:hover {
  color: #ffffff;
  background: rgba(107, 70, 193, 0.15);
}

.user-dropdown-menu .el-dropdown-menu__item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>
