<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowLeft,
  Clock,
  CollectionTag,
  Star,
  Collection,
  CaretRight,
  VideoPlay,
  Headset,
  ArrowDown,
  User,
  House,
  SwitchButton,
  Setting,
  CircleCheckFilled,
  CirclePlus,
  Plus,
  MoreFilled,
  EditPen,
  Delete
} from '@element-plus/icons-vue'
import { logout as logoutApi } from '@/api/user'
import { addPlaylist, updatePlaylist, deletePlaylist, removeSongFromPlaylist } from '@/api/playlist'
import { getUser, clearAuth, setUser } from '@/utils/authStorage'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useProfileDetail } from './useProfileDetail'
import PlaylistFormDialog from './PlaylistFormDialog.vue'
import AddToPlaylistDialog from './AddToPlaylistDialog.vue'
import type { DetailTab, SongListType } from './useProfileDetail'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { MusicVO } from '@/types/music'

const router = useRouter()

const {
  currentTab,
  pageTitle,
  loading,
  historyList,
  historyPageNum,
  historyPageSize,
  historyTotal,
  playlistList,
  playlistPageNum,
  playlistPageSize,
  playlistTotal,
  collectedPlaylistList,
  collectedPlaylistPageNum,
  collectedPlaylistPageSize,
  collectedPlaylistTotal,
  collectedAlbumList,
  collectedAlbumPageNum,
  collectedAlbumPageSize,
  collectedAlbumTotal,
  songList,
  songListPageData,
  collectMusicIds,
  loadCurrentTab,
  enterSongList,
  backFromSongList,
  playMusic,
  formatPlayedAt,
  handleUncollectPlaylist,
  handleUncollectAlbum
} = useProfileDetail()

// 歌单表单弹窗
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const dialogInitialData = ref<Partial<PlaylistVO>>({})

// 添加到歌单弹窗
const addDialogVisible = ref(false)
const addDialogMusicId = ref(0)

function openAddToPlaylistDialog(musicId: number) {
  addDialogMusicId.value = musicId
  addDialogVisible.value = true
}

const canRemoveFromPlaylist = computed(() =>
  currentTab.value === 'playlists' && songList.value.type === 'playlist'
)

async function handleRemoveFromPlaylist(musicId: number) {
  if (!canRemoveFromPlaylist.value) return
  try {
    const newCollectMusicIds = await removeSongFromPlaylist(songList.value.id, musicId)
    // 更新本地用户数据
    const u = getUser()
    if (u) {
      u.collectMusicIds = newCollectMusicIds
      u.collectMusicCount = newCollectMusicIds.length
      setUser(u)
    }
    ElMessage.success('已从歌单移除')
    // 刷新歌曲列表
    enterSongList('playlist', songList.value.id, songList.value.name)
  } catch (err: any) {
    ElMessage.error(err.message || '移除失败')
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  dialogInitialData.value = {}
  dialogVisible.value = true
}

function openEditDialog(pl: PlaylistVO) {
  dialogMode.value = 'edit'
  dialogInitialData.value = {
    id: pl.id,
    playlistName: pl.playlistName,
    imageUrl: pl.imageUrl,
    isPrivate: pl.isPrivate
  }
  dialogVisible.value = true
}

async function handleDialogSubmit(data: Partial<PlaylistVO>) {
  try {
    if (dialogMode.value === 'create') {
      await addPlaylist(data)
      ElMessage.success('创建成功')
    } else {
      await updatePlaylist(data as Required<Pick<PlaylistVO, 'id'>> & Partial<PlaylistVO>)
      ElMessage.success('修改成功')
    }
    dialogVisible.value = false
    loadCurrentTab()
  } catch {
    ElMessage.error(dialogMode.value === 'create' ? '创建失败' : '修改失败')
  }
}

async function handleDeletePlaylist(id: number) {
  try {
    await ElMessageBox.confirm('确定要删除这个歌单吗？', '删除歌单', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deletePlaylist(id)
    ElMessage.success('删除成功')
    loadCurrentTab()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

const user = computed(() => getUser())
const displayName = computed(() => user.value?.name || user.value?.username || '用户')
const avatarUrl = computed(() => user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png')
const isAdmin = computed(() => (user.value?.role ?? 0) >= 2)

const tabs: { key: DetailTab; label: string; icon: any }[] = [
  { key: 'history', label: '听歌历史', icon: Clock },
  { key: 'playlists', label: '我的歌单', icon: CollectionTag },
  { key: 'collected-playlists', label: '收藏歌单', icon: Star },
  { key: 'collected-albums', label: '收藏专辑', icon: Collection }
]

function goBack() {
  router.push('/profile')
}

function switchTab(tab: DetailTab) {
  const pathMap: Record<DetailTab, string> = {
    history: '/profile/history',
    playlists: '/profile/playlists',
    'collected-playlists': '/profile/collected-playlists',
    'collected-albums': '/profile/collected-albums'
  }
  router.push(pathMap[tab])
}

function onPlaylistClick(pl: PlaylistVO) {
  enterSongList('playlist', pl.id, pl.playlistName)
}

function onAlbumClick(album: AlbumVO) {
  enterSongList('album', album.id, album.albumName)
}

function formatCount(count: number): string {
  if (count >= 10000) {
    return (count / 10000).toFixed(1) + '万'
  }
  return count.toLocaleString()
}

function isMusicCollected(musicId: number): boolean {
  return collectMusicIds.value.has(musicId)
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

function goHome() {
  router.push('/home')
}

function goProfile() {
  router.push('/profile')
}

function goAdmin() {
  router.push('/admin')
}
</script>

<template>
  <div class="profile-detail-page">
    <!-- 背景光晕层 -->
    <div class="detail-bg-glow" aria-hidden="true" />
    <!-- 星尘点缀 -->
    <div class="detail-stars" aria-hidden="true">
      <span v-for="i in 5" :key="i" class="star-dot" :class="`star-${i}`" />
    </div>
    <!-- 页面头部 -->
    <header class="detail-header">
      <div class="header-inner">
        <div class="header-left">
          <div class="back-btn" @click="goBack">
            <el-icon size="18"><ArrowLeft /></el-icon>
            <span>返回</span>
          </div>
          <div class="header-divider" />
          <div class="page-title">
            <div class="title-icon">
              <div class="sound-wave-mini">
                <span v-for="i in 4" :key="i" class="wave-bar-mini" />
              </div>
            </div>
            <span>{{ pageTitle }}</span>
          </div>
        </div>

        <!-- 用户头像下拉 -->
        <el-dropdown trigger="click" popper-class="detail-dropdown-popper">
          <div class="header-avatar">
            <el-avatar :size="36" :src="avatarUrl" class="user-avatar-mini" />
            <el-icon size="12" class="avatar-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="detail-dropdown-menu">
              <div class="dropdown-header">
                <el-avatar :size="48" :src="avatarUrl" />
                <div class="dropdown-meta">
                  <div class="dropdown-name">{{ displayName }}</div>
                  <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                </div>
              </div>
              <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
              <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goAdmin">管理后台</el-dropdown-item>
              <el-dropdown-item :icon="House" @click="goHome">返回首页</el-dropdown-item>
              <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- Tab 导航 -->
    <nav class="tab-nav">
      <div class="tab-nav-inner">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: currentTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <el-icon size="16"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.label }}</span>
          <div class="tab-indicator" />
        </div>
      </div>
    </nav>

    <!-- 内容区域 -->
    <main v-loading="loading" class="detail-content">
      <!-- 听歌历史 -->
      <template v-if="currentTab === 'history' && !songList.show">
        <div class="history-list">
          <div
            v-for="(item, index) in historyList"
            :key="item.id"
            class="history-item"
            :style="{ animationDelay: `${index * 0.04}s` }"
          >
            <div class="history-rank">{{ (historyPageNum - 1) * historyPageSize + index + 1 }}</div>
            <div class="history-cover">
              <img v-if="item.coverUrl" :src="item.coverUrl" :alt="item.musicName" />
              <div v-else class="cover-placeholder">
                <el-icon size="18"><Headset /></el-icon>
              </div>
            </div>
            <div class="history-info">
              <div class="history-name">{{ item.musicName || '未知歌曲' }}</div>
              <div class="history-meta">
                <span>{{ item.authorNames?.filter(Boolean).join(' / ') || '未知作者' }}</span>
                <template v-if="item.albumName">
                  <span class="meta-dot">·</span>
                  <span>{{ item.albumName }}</span>
                </template>
              </div>
            </div>
            <div class="history-time">{{ formatPlayedAt(item.playedAt) }}</div>
            <div class="history-actions">
              <button class="action-btn play" @click="playMusic({
                id: item.songId || 0,
                musicName: item.musicName || '',
                authorNameList: item.authorNames || [],
                image1Url: item.coverUrl || '',
                fileUrl: item.fileUrl || ''
              } as MusicVO)">
                <el-icon size="16"><CaretRight /></el-icon>
              </button>
              <button
                class="action-btn collect"
                :class="{ collected: isMusicCollected(item.songId || 0) }"
                @click="openAddToPlaylistDialog(item.songId || 0)"
              >
                <el-icon size="16">
                  <CircleCheckFilled v-if="isMusicCollected(item.songId || 0)" />
                  <CirclePlus v-else />
                </el-icon>
              </button>
            </div>
          </div>
          <div v-if="historyList.length === 0" class="empty-state">
            <el-icon size="40" color="#475569"><Clock /></el-icon>
            <span>暂无播放记录</span>
          </div>
        </div>
        <div v-if="historyTotal > 0" class="pagination-bar">
          <el-pagination
            v-model:current-page="historyPageNum"
            v-model:page-size="historyPageSize"
            :total="historyTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </template>

      <!-- 我的歌单 -->
      <template v-if="currentTab === 'playlists' && !songList.show">
        <div class="playlist-toolbar">
          <span class="toolbar-count">共 {{ playlistTotal }} 个歌单</span>
          <button class="create-playlist-btn" @click="openCreateDialog">
            <el-icon size="14"><Plus /></el-icon>
            <span>创建歌单</span>
          </button>
        </div>
        <div class="card-grid">
          <div
            v-for="(pl, index) in playlistList"
            :key="pl.id"
            class="media-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
            @click="onPlaylistClick(pl)"
          >
            <div class="media-cover">
              <el-icon v-if="!pl.imageUrl" size="36"><CollectionTag /></el-icon>
              <img v-else :src="pl.imageUrl" :alt="pl.playlistName" />
              <div class="media-play-overlay">
                <div class="media-play-btn">
                  <el-icon size="20"><CaretRight /></el-icon>
                </div>
              </div>
              <div class="media-badge">{{ pl.songIds?.length || 0 }}首</div>
            </div>
            <el-dropdown
              trigger="click"
              popper-class="card-dropdown-popper"
              class="edit-dropdown"
              @click.stop
            >
              <button class="media-edit-btn" @click.stop>
                <el-icon size="14"><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu class="card-dropdown-menu">
                  <el-dropdown-item :icon="EditPen" @click="openEditDialog(pl)">
                    编辑歌单信息
                  </el-dropdown-item>
                  <el-dropdown-item :icon="Delete" @click="handleDeletePlaylist(pl.id)">
                    删除歌单
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <div class="media-info">
              <div class="media-name">{{ pl.playlistName }}</div>
              <div class="media-desc">{{ formatCount(pl.playCount || 0) }}次播放</div>
            </div>
          </div>
          <div v-if="playlistList.length === 0" class="empty-state">
            <el-icon size="40" color="#475569"><CollectionTag /></el-icon>
            <span>暂无创建的歌单</span>
          </div>
        </div>
        <div v-if="playlistTotal > 0" class="pagination-bar">
          <el-pagination
            v-model:current-page="playlistPageNum"
            v-model:page-size="playlistPageSize"
            :total="playlistTotal"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </template>

      <!-- 收藏歌单 -->
      <template v-if="currentTab === 'collected-playlists' && !songList.show">
        <div class="card-grid">
          <div
            v-for="(pl, index) in collectedPlaylistList"
            :key="pl.id"
            class="media-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
            @click="onPlaylistClick(pl)"
          >
            <div class="media-cover">
              <el-icon v-if="!pl.imageUrl" size="36"><Star /></el-icon>
              <img v-else :src="pl.imageUrl" :alt="pl.playlistName" />
              <div class="media-play-overlay">
                <div class="media-play-btn">
                  <el-icon size="20"><CaretRight /></el-icon>
                </div>
              </div>
              <div class="media-badge">{{ pl.songIds?.length || 0 }}首</div>
              <el-dropdown
                trigger="click"
                popper-class="card-dropdown-popper"
                class="edit-dropdown"
                @click.stop
              >
                <button class="media-edit-btn" @click.stop>
                  <el-icon size="14"><MoreFilled /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="card-dropdown-menu">
                    <el-dropdown-item :icon="Delete" @click="handleUncollectPlaylist(pl.id)">
                      取消收藏
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <div class="media-info">
              <div class="media-name">{{ pl.playlistName }}</div>
              <div class="media-desc">{{ formatCount(pl.playCount || 0) }}次播放</div>
            </div>
          </div>
          <div v-if="collectedPlaylistList.length === 0" class="empty-state">
            <el-icon size="40" color="#475569"><Star /></el-icon>
            <span>暂无收藏的歌单</span>
          </div>
        </div>
        <div v-if="collectedPlaylistTotal > 0" class="pagination-bar">
          <el-pagination
            v-model:current-page="collectedPlaylistPageNum"
            v-model:page-size="collectedPlaylistPageSize"
            :total="collectedPlaylistTotal"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </template>

      <!-- 收藏专辑 -->
      <template v-if="currentTab === 'collected-albums' && !songList.show">
        <div class="card-grid">
          <div
            v-for="(album, index) in collectedAlbumList"
            :key="album.id"
            class="media-card album-card"
            :style="{ animationDelay: `${index * 0.05}s` }"
            @click="onAlbumClick(album)"
          >
            <div class="media-cover album-cover">
              <el-icon v-if="!album.image1Url" size="36"><Collection /></el-icon>
              <img v-else :src="album.image1Url" :alt="album.albumName" />
              <div class="media-play-overlay">
                <div class="media-play-btn">
                  <el-icon size="20"><CaretRight /></el-icon>
                </div>
              </div>
              <div class="media-badge">{{ album.songIds?.length || 0 }}首</div>
              <el-dropdown
                trigger="click"
                popper-class="card-dropdown-popper"
                class="edit-dropdown"
                @click.stop
              >
                <button class="media-edit-btn" @click.stop>
                  <el-icon size="14"><MoreFilled /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="card-dropdown-menu">
                    <el-dropdown-item :icon="Delete" @click="handleUncollectAlbum(album.id)">
                      取消收藏
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            <div class="media-info">
              <div class="media-name">{{ album.albumName }}</div>
              <div class="media-desc">{{ album.authorNames?.filter(Boolean).join(' / ') || '未知艺人' }}</div>
            </div>
          </div>
          <div v-if="collectedAlbumList.length === 0" class="empty-state">
            <el-icon size="40" color="#475569"><Collection /></el-icon>
            <span>暂无收藏的专辑</span>
          </div>
        </div>
        <div v-if="collectedAlbumTotal > 0" class="pagination-bar">
          <el-pagination
            v-model:current-page="collectedAlbumPageNum"
            v-model:page-size="collectedAlbumPageSize"
            :total="collectedAlbumTotal"
            :page-sizes="[12, 24, 48]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </template>

      <!-- 歌曲列表视图 -->
      <div v-if="songList.show" class="song-list-view">
        <div class="song-list-header">
          <button class="back-btn-secondary" @click="backFromSongList">
            <el-icon size="16"><ArrowLeft /></el-icon>
            <span>返回</span>
          </button>
          <h2 class="song-list-title">{{ songList.name }}</h2>
          <span class="song-list-count">{{ songList.total }}首歌曲</span>
        </div>

        <div v-loading="songList.loading" class="song-list-body">
          <div
            v-for="(music, index) in songListPageData"
            :key="music.id"
            class="song-item"
            :style="{ animationDelay: `${index * 0.03}s` }"
          >
            <div class="song-rank">{{ (songList.pageNum - 1) * songList.pageSize + index + 1 }}</div>
            <div class="song-cover-small">
              <img v-if="music.image1Url" :src="music.image1Url" :alt="music.musicName" />
              <div v-else class="cover-placeholder-small">
                <el-icon size="14"><Headset /></el-icon>
              </div>
            </div>
            <div class="song-info-main">
              <div class="song-name-main">{{ music.musicName }}</div>
              <div class="song-meta-main">
                <span>{{ music.authorNameList?.filter(Boolean).join(' / ') || '未知作者' }}</span>
                <template v-if="music.albumName">
                  <span class="meta-dot">·</span>
                  <span>{{ music.albumName }}</span>
                </template>
              </div>
            </div>
            <div class="song-actions">
              <button class="action-btn play" @click="playMusic(music)">
                <el-icon size="16"><VideoPlay /></el-icon>
              </button>
              <el-dropdown trigger="click" popper-class="song-action-dropdown">
                <button
                  class="action-btn collect"
                  :class="{ collected: isMusicCollected(music.id) }"
                >
                  <el-icon size="16">
                    <CircleCheckFilled v-if="isMusicCollected(music.id)" />
                    <CirclePlus v-else />
                  </el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu class="song-action-menu">
                    <el-dropdown-item @click="openAddToPlaylistDialog(music.id)">
                      收藏到歌单
                    </el-dropdown-item>
                    <el-dropdown-item v-if="canRemoveFromPlaylist" @click="handleRemoveFromPlaylist(music.id)">
                      取消收藏
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <div v-if="songList.songs.length === 0 && !songList.loading" class="empty-state">
            <el-icon size="40" color="#475569"><Headset /></el-icon>
            <span>暂无歌曲</span>
          </div>
        </div>

        <div v-if="songList.total > 0" class="pagination-bar">
          <el-pagination
            v-model:current-page="songList.pageNum"
            v-model:page-size="songList.pageSize"
            :total="songList.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            background
          />
        </div>
      </div>
    </main>

    <PlaylistFormDialog
      :visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="dialogInitialData"
      @submit="handleDialogSubmit"
      @cancel="dialogVisible = false"
    />

    <AddToPlaylistDialog
      :visible="addDialogVisible"
      :music-id="addDialogMusicId"
      @submit="addDialogVisible = false"
      @cancel="addDialogVisible = false"
    />
  </div>
</template>

<style scoped src="./profile-detail.css"></style>

<style>
/* Dropdown popper styles (global) */
.detail-dropdown-popper {
  --el-dropdown-menuItem-hover-fill: rgba(107, 70, 193, 0.15);
  --el-dropdown-menuItem-hover-color: #e2e8f0;
}

.detail-dropdown-menu {
  background: linear-gradient(135deg, #1a1025 0%, #2d1b4e 100%) !important;
  border: 1px solid rgba(107, 70, 193, 0.15) !important;
  border-radius: 16px !important;
  padding: 8px !important;
  min-width: 200px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.detail-dropdown-menu .dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.detail-dropdown-menu .dropdown-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-dropdown-menu .dropdown-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.detail-dropdown-menu .dropdown-level {
  font-size: 12px;
  color: #ec4899;
  font-weight: 500;
}

.detail-dropdown-menu .el-dropdown-menu__item {
  color: #94a3b8;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
}

.detail-dropdown-menu .el-dropdown-menu__item:hover {
  color: #e2e8f0;
  background: rgba(107, 70, 193, 0.15);
}

.detail-dropdown-menu .el-dropdown-menu__item .el-icon {
  margin-right: 8px;
  font-size: 16px;
}
</style>
