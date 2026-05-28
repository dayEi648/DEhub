<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMusicById } from '@/api/music'
import { addPlaylist, updatePlaylist, deletePlaylist } from '@/api/playlist'
import {
  Clock,
  Headset,
  CaretRight,
  ArrowRight,
  CollectionTag,
  Collection,
  Star,
  Plus,
  MoreFilled,
  EditPen,
  Delete
} from '@element-plus/icons-vue'
import { useProfileFavorites } from './useProfileFavorites'
import type { RecentSong } from './useProfileFavorites'
import PlaylistFormDialog from './PlaylistFormDialog.vue'

const router = useRouter()
const playerStore = usePlayerStore()

const {
  loading,
  recentSongs,
  myPlaylists,
  collectedPlaylists,
  collectedAlbums,
  loadMyPlaylists,
  handleUncollectPlaylist,
  handleUncollectAlbum
} = useProfileFavorites()

// 歌单表单弹窗
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const dialogInitialData = ref<Partial<any>>({})

function openCreateDialog() {
  dialogMode.value = 'create'
  dialogInitialData.value = {}
  dialogVisible.value = true
}

function openEditDialog(pl: any) {
  dialogMode.value = 'edit'
  dialogInitialData.value = {
    id: pl.id,
    playlistName: pl.name,
    imageUrl: pl.cover,
    isPrivate: pl.isPrivate ?? false
  }
  dialogVisible.value = true
}

async function handleDialogSubmit(data: Partial<any>) {
  try {
    if (dialogMode.value === 'create') {
      await addPlaylist(data)
      ElMessage.success('创建成功')
    } else {
      await updatePlaylist(data as any)
      ElMessage.success('修改成功')
    }
    dialogVisible.value = false
    loadMyPlaylists()
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
    loadMyPlaylists()
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '删除失败')
    }
  }
}

function goToPlaylist(pl: any) {
  router.push({
    path: '/profile/playlists',
    query: { openId: pl.id, openName: encodeURIComponent(pl.name) }
  })
}

async function onPlay(song: RecentSong) {
  try {
    const music = await getMusicById(song.id)
    if (!music.fileUrl) {
      ElMessage.warning('暂无播放资源')
      return
    }
    const ok = playerStore.playTrack({
      id: music.id,
      name: music.musicName,
      artist: music.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
      coverUrl: music.image1Url || '',
      fileUrl: music.fileUrl,
      duration: 0,
      currentTime: 0,
      vip: music.vip
    }, true)
    if (!ok) return
    playerStore.showBar()
    router.push(`/music/${music.id}`)
  } catch {
    ElMessage.error('获取歌曲信息失败')
  }
}

</script>

<template>
  <div v-loading="loading" class="favorites-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">我的收藏</h1>
      <p class="page-subtitle">管理你的音乐收藏与播放记录</p>
    </div>

    <!-- 最近听歌 -->
    <section class="content-section">
      <div class="section-header">
        <div class="section-title-wrap">
          <el-icon class="section-icon" size="18"><Clock /></el-icon>
          <h2 class="section-title">最近听歌</h2>
        </div>
        <router-link class="section-more" to="/profile/history">
          全部记录
          <el-icon size="14"><ArrowRight /></el-icon>
        </router-link>
      </div>
      <div class="recent-songs-scroll">
        <div
          v-for="(song, index) in recentSongs"
          :key="song.id"
          class="recent-song-card"
          :style="{ animationDelay: `${index * 0.05}s` }"
          @click="onPlay(song)"
        >
          <div class="song-cover">
            <img v-if="song.cover" :src="song.cover" :alt="song.name" />
            <div v-else class="cover-placeholder">
              <el-icon size="20"><Headset /></el-icon>
            </div>
            <div class="song-play-overlay">
              <div class="song-play-btn">
                <el-icon size="24"><CaretRight /></el-icon>
              </div>
            </div>
          </div>
          <div class="song-info">
            <div class="song-name">{{ song.name }}</div>
            <div class="song-time">{{ song.playedAt }}</div>
          </div>
        </div>
        <div v-if="recentSongs.length === 0" class="empty-tip">
          <el-icon size="32" color="#475569"><Clock /></el-icon>
          <span>暂无播放记录</span>
        </div>
      </div>
    </section>

    <!-- 我的歌单 -->
    <section class="content-section">
      <div class="section-header">
        <div class="section-title-wrap">
          <el-icon class="section-icon" size="18"><CollectionTag /></el-icon>
          <h2 class="section-title">我的歌单</h2>
        </div>
        <div class="section-actions">
          <button class="create-playlist-btn" @click="openCreateDialog">
            <el-icon size="14"><Plus /></el-icon>
            <span>创建歌单</span>
          </button>
          <router-link class="section-more" to="/profile/playlists">
            全部歌单
            <el-icon size="14"><ArrowRight /></el-icon>
          </router-link>
        </div>
      </div>
      <div class="card-grid">
        <div
          v-for="(pl, index) in myPlaylists"
          :key="pl.id"
          class="playlist-card"
          :style="{ animationDelay: `${index * 0.06}s` }"
          @click="goToPlaylist(pl)"
        >
          <div class="card-cover">
            <el-icon v-if="!pl.cover" size="32"><Headset /></el-icon>
            <img v-else :src="pl.cover" :alt="pl.name" />
            <div class="card-play-overlay">
              <div class="card-play-btn">
                <el-icon size="20"><CaretRight /></el-icon>
              </div>
            </div>
          </div>
          <el-dropdown
            trigger="click"
            popper-class="card-dropdown-popper"
            class="edit-dropdown"
            @click.stop
          >
            <button class="card-edit-btn" @click.stop>
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
          <div class="card-info">
            <div class="card-name">{{ pl.name }}</div>
            <div class="card-meta">
              <span>{{ pl.songCount }}首</span>
              <span class="meta-divider">·</span>
              <span>{{ pl.playCount }}次播放</span>
            </div>
          </div>
        </div>
        <div v-if="myPlaylists.length === 0" class="empty-tip">
          <el-icon size="32" color="#475569"><CollectionTag /></el-icon>
          <span>暂无创建的歌单</span>
        </div>
      </div>
    </section>

    <!-- 收藏歌单 -->
    <section class="content-section">
      <div class="section-header">
        <div class="section-title-wrap">
          <el-icon class="section-icon" size="18"><Star /></el-icon>
          <h2 class="section-title">收藏歌单</h2>
        </div>
        <router-link class="section-more" to="/profile/collected-playlists">
          全部收藏
          <el-icon size="14"><ArrowRight /></el-icon>
        </router-link>
      </div>
      <div class="card-grid">
        <div
          v-for="(pl, index) in collectedPlaylists"
          :key="pl.id"
          class="playlist-card"
          :style="{ animationDelay: `${index * 0.06}s` }"
          @click="router.push('/profile/collected-playlists')"
        >
          <div class="card-cover">
            <el-icon v-if="!pl.cover" size="32"><Star /></el-icon>
            <img v-else :src="pl.cover" :alt="pl.name" />
            <div class="card-play-overlay">
              <div class="card-play-btn">
                <el-icon size="20"><CaretRight /></el-icon>
              </div>
            </div>
            <el-dropdown
              trigger="click"
              popper-class="card-dropdown-popper"
              class="edit-dropdown"
              @click.stop
            >
              <button class="card-edit-btn" @click.stop>
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
          <div class="card-info">
            <div class="card-name">{{ pl.name }}</div>
            <div class="card-meta">
              <span>{{ pl.songCount }}首</span>
              <span class="meta-divider">·</span>
              <span>{{ pl.playCount }}次播放</span>
            </div>
          </div>
        </div>
        <div v-if="collectedPlaylists.length === 0" class="empty-tip">
          <el-icon size="32" color="#475569"><Star /></el-icon>
          <span>暂无收藏的歌单</span>
        </div>
      </div>
    </section>

    <!-- 收藏专辑 -->
    <section class="content-section">
      <div class="section-header">
        <div class="section-title-wrap">
          <el-icon class="section-icon" size="18"><Collection /></el-icon>
          <h2 class="section-title">收藏专辑</h2>
        </div>
        <router-link class="section-more" to="/profile/collected-albums">
          全部收藏
          <el-icon size="14"><ArrowRight /></el-icon>
        </router-link>
      </div>
      <div class="card-grid">
        <div
          v-for="(album, index) in collectedAlbums"
          :key="album.id"
          class="album-card"
          :style="{ animationDelay: `${index * 0.06}s` }"
          @click="router.push('/profile/collected-albums')"
        >
          <div class="card-cover album-cover">
            <el-icon v-if="!album.cover" size="32"><Collection /></el-icon>
            <img v-else :src="album.cover" :alt="album.name" />
            <div class="card-play-overlay">
              <div class="card-play-btn">
                <el-icon size="20"><CaretRight /></el-icon>
              </div>
            </div>
            <el-dropdown
              trigger="click"
              popper-class="card-dropdown-popper"
              class="edit-dropdown"
              @click.stop
            >
              <button class="card-edit-btn" @click.stop>
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
          <div class="card-info">
            <div class="card-name">{{ album.name }}</div>
            <div class="card-meta">
              <span>{{ album.artist }}</span>
              <span class="meta-divider">·</span>
              <span>{{ album.year }}</span>
            </div>
          </div>
        </div>
        <div v-if="collectedAlbums.length === 0" class="empty-tip">
          <el-icon size="32" color="#475569"><Collection /></el-icon>
          <span>暂无收藏的专辑</span>
        </div>
      </div>
    </section>

    <PlaylistFormDialog
      :visible="dialogVisible"
      :mode="dialogMode"
      :initial-data="dialogInitialData"
      @submit="handleDialogSubmit"
      @cancel="dialogVisible = false"
    />
  </div>
</template>

<style scoped src="./profile-favorites.css"></style>
