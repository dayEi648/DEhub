<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Headset, Document, List, User, Setting, SwitchButton, ArrowDown, House } from '@element-plus/icons-vue'
import NotificationBell from '@/components/NotificationBell/NotificationBell.vue'
import CommentSection from '@/components/CommentSection/CommentSection.vue'
import { usePlayerPage } from './usePlayerPage'
import { usePlayerStore } from '@/stores/player'
import { useLyrics } from '@/composables/useLyrics'
import { getUser, clearAuth } from '@/utils/authStorage'
import type { MusicVO } from '@/types/music'
import type { PlaylistVO } from '@/types/playlist'

const {
  music,
  loading,
  error,
  activeTab,
  recommendPlaylists,
  recommendMusics,
  recommendLoading,
  goBack,
  goToMusic
} = usePlayerPage()

const router = useRouter()
const playerStore = usePlayerStore()

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

function handleLogout() {
  clearAuth()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const tabs = [
  { key: 'lyrics' as const, label: '歌词', icon: Document },
  { key: 'details' as const, label: '详情', icon: Headset },
  { key: 'similar' as const, label: '相似推荐', icon: List }
]

const coverUrl = computed(() => {
  return music.value?.image2Url || music.value?.image1Url || ''
})

const isPlayingCurrent = computed(() => {
  return playerStore.isPlaying && playerStore.currentTrack?.id === music.value?.id
})

// 歌词
const lyricsContainerRef = ref<HTMLElement | null>(null)
const musicId = computed(() => music.value?.id)
const { lines: lyricLines, loading: lyricLoading, error: lyricError, findCurrentLineIndex } = useLyrics(musicId)

const currentLineIndex = computed(() => {
  if (!music.value) return -1
  return findCurrentLineIndex(playerStore.currentTrack.currentTime)
})

watch(currentLineIndex, () => {
  nextTick(() => {
    if (!lyricsContainerRef.value) return
    const el = lyricsContainerRef.value.querySelector('.lyric-line.active') as HTMLElement | null
    if (el) {
      const container = lyricsContainerRef.value
      const containerRect = container.getBoundingClientRect()
      const elRect = el.getBoundingClientRect()
      const relativeTop = elRect.top - containerRect.top + container.scrollTop
      container.scrollTo({
        top: relativeTop - container.clientHeight / 2 + el.clientHeight / 2,
        behavior: 'smooth'
      })
    }
  })
})

// 进度条
const progressValue = computed({
  get: () => playerStore.progressPercent,
  set: (val: number) => {
    const time = (val / 100) * playerStore.currentTrack.duration
    playerStore.seek(time)
  }
})

function onPlayCurrent() {
  if (!music.value) return
  const isSame = playerStore.currentTrack.id === music.value.id
  if (isSame) {
    playerStore.togglePlay()
  } else {
    const ok = playerStore.playTrack({
      id: music.value.id,
      name: music.value.musicName,
      artist: (music.value.authorNameList || []).join(' / ') || '未知歌手',
      coverUrl: music.value.image1Url || '',
      fileUrl: music.value.fileUrl || '',
      duration: 0,
      currentTime: 0,
      vip: music.value.vip
    }, true)
    if (!ok) return
    playerStore.showBar()
  }
}

function onPlaySimilar(sm: MusicVO) {
  const ok = playerStore.playTrack({
    id: sm.id,
    name: sm.musicName,
    artist: (sm.authorNameList || []).join(' / ') || '未知歌手',
    coverUrl: sm.image1Url || '',
    fileUrl: sm.fileUrl || '',
    vip: sm.vip,
    duration: 0,
    currentTime: 0
  }, true)
  if (!ok) return
  playerStore.showBar()
  router.replace(`/music/${sm.id}`)
}

function formatTime(time?: string) {
  if (!time) return ''
  return time.replace('T', ' ').slice(0, 16)
}

function joinNames(names?: string[]) {
  return names?.filter(Boolean).join(' / ') || '未知歌手'
}

function formatTags(tags?: string[]) {
  return tags?.filter(Boolean).join('、') || '-'
}
</script>

<template>
  <div class="player-page">
    <!-- 动态氛围背景层 -->
    <div class="player-bg" :style="{ backgroundImage: `url(${coverUrl})` }"></div>
    <!-- 紫色光晕层 -->
    <div class="player-bg-glow" aria-hidden="true"></div>
    <!-- 音律装饰层 -->
    <div class="player-sound-waves" aria-hidden="true">
      <span v-for="i in 16" :key="i" class="wave-bar" :style="{ animationDelay: `${(i - 1) * 0.12}s`, height: `${18 + Math.random() * 72}%` }" />
    </div>

    <!-- 顶部栏 -->
    <div class="player-header">
      <button class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <h1 class="player-title">{{ music?.musicName || '音乐播放' }}</h1>

      <!-- 右侧用户区 -->
      <div class="header-user">
        <NotificationBell />
        <el-dropdown trigger="click" popper-class="player-dropdown-popper">
          <div class="user-card">
            <el-avatar :size="32" :src="avatarUrl" class="user-avatar" />
            <span class="user-name">{{ displayName }}</span>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu class="player-dropdown-menu">
              <div class="dropdown-header">
                <el-avatar :size="40" :src="avatarUrl" />
                <div class="dropdown-meta">
                  <div class="dropdown-name">{{ displayName }}</div>
                  <div class="dropdown-level">Lv.{{ user?.level || 1 }}</div>
                </div>
              </div>
              <el-dropdown-item :icon="User" @click="goProfile">个人中心</el-dropdown-item>
              <el-dropdown-item :icon="House" @click="goHome">回到主页</el-dropdown-item>
              <el-dropdown-item v-if="isAdmin" :icon="Setting" @click="goHome">管理后台</el-dropdown-item>
              <el-dropdown-item divided :icon="SwitchButton" @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="player-loading">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="player-error">
      <el-icon :size="48"><Headset /></el-icon>
      <p>{{ error }}</p>
    </div>

    <!-- 主内容 -->
    <template v-else-if="music">
      <div class="player-body">
        <!-- 左侧：封面 -->
        <div class="cover-section">
          <div class="cover-wrapper" :class="{ spinning: isPlayingCurrent }">
            <img
              v-if="coverUrl"
              :src="coverUrl"
              :alt="music.musicName"
              class="cover-img"
            />
            <div v-else class="cover-placeholder">
              <el-icon :size="64"><Headset /></el-icon>
            </div>
          </div>
          <!-- 播放控制 -->
          <div class="cover-controls">
            <button class="cover-play-btn" @click="onPlayCurrent">
              <svg v-if="!isPlayingCurrent" viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <path d="M8 5.14v13.72a1 1 0 001.5.86l11-6.86a1 1 0 000-1.72l-11-6.86a1 1 0 00-1.5.86z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <rect x="6" y="4" width="4" height="16" rx="1"/>
                <rect x="14" y="4" width="4" height="16" rx="1"/>
              </svg>
            </button>
            <div class="cover-progress">
              <span class="cover-time">{{ playerStore.formattedCurrentTime }}</span>
              <el-slider v-model="progressValue" :max="100" :show-tooltip="false" class="cover-progress-slider" />
              <span class="cover-time">{{ playerStore.formattedDuration }}</span>
            </div>
          </div>
        </div>

        <!-- 右侧：信息与控制 -->
        <div class="info-section">
          <!-- 基本信息 -->
          <div class="music-meta">
            <h2 class="music-name">{{ music.musicName }}</h2>
            <div class="meta-row">
              <span class="meta-item">
                <el-icon><Headset /></el-icon>
                {{ joinNames(music.authorNameList) }}
              </span>
              <span v-if="music.albumName" class="meta-item">
                专辑：{{ music.albumName }}
              </span>
              <span v-if="music.source" class="meta-item">
                来源：{{ music.source }}
              </span>
            </div>
          </div>

          <!-- Tab 切换 -->
          <div class="tab-bar">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              {{ tab.label }}
            </button>
          </div>

          <!-- Tab 内容 -->
          <div class="tab-content">
            <!-- 歌词 -->
            <div v-if="activeTab === 'lyrics'" class="tab-panel lyrics-panel" ref="lyricsContainerRef">
              <div v-if="lyricLoading" class="lyrics-loading">
                <el-skeleton :rows="8" animated />
              </div>
              <div v-else-if="lyricError" class="lyrics-empty">
                <el-icon :size="32"><Document /></el-icon>
                <p>{{ lyricError }}</p>
              </div>
              <div v-else-if="lyricLines.length === 0" class="lyrics-empty">
                <el-icon :size="32"><Document /></el-icon>
                <p>暂无歌词</p>
              </div>
              <div v-else class="lyrics-list">
                <div
                  v-for="(line, index) in lyricLines"
                  :key="index"
                  class="lyric-line"
                  :class="{ active: index === currentLineIndex }"
                >
                  {{ line.text }}
                </div>
              </div>
            </div>

            <!-- 详情 -->
            <div v-if="activeTab === 'details'" class="tab-panel">
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">风格</span>
                  <span class="detail-value">{{ music.style || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">语言</span>
                  <span class="detail-value">{{ formatTags(music.languages) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">乐器</span>
                  <span class="detail-value">{{ formatTags(music.instruments) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">情绪标签</span>
                  <span class="detail-value">{{ formatTags(music.emoTags) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">兴趣标签</span>
                  <span class="detail-value">{{ formatTags(music.interestTags) }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">发行日期</span>
                  <span class="detail-value">{{ music.releaseDate || '-' }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">热度</span>
                  <span class="detail-value">{{ music.hot ?? 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">播放量</span>
                  <span class="detail-value">{{ music.playCount ?? 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">收藏数</span>
                  <span class="detail-value">{{ music.collectCount ?? 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">评论数</span>
                  <span class="detail-value">{{ music.commentCount ?? 0 }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">VIP</span>
                  <span class="detail-value">{{ music.vip ? '是' : '否' }}</span>
                </div>
              </div>
            </div>

            <!-- 相似推荐 -->
            <div v-if="activeTab === 'similar'" class="tab-panel">
              <div v-if="recommendLoading" class="recommend-loading">
                <el-skeleton :rows="4" animated />
              </div>
              <template v-else>
                <!-- 推荐歌单 -->
                <div v-if="recommendPlaylists.length > 0" class="recommend-section">
                  <h3 class="recommend-title">包含此歌的歌单</h3>
                  <div class="playlist-grid">
                    <div
                      v-for="pl in recommendPlaylists"
                      :key="pl.id"
                      class="playlist-card"
                      @click="router.push(`/playlist/${pl.id}`)"
                    >
                      <div class="playlist-cover">
                        <img v-if="pl.imageUrl" :src="pl.imageUrl" :alt="pl.playlistName" />
                        <div v-else class="playlist-cover-placeholder">
                          <el-icon><Headset /></el-icon>
                        </div>
                      </div>
                      <div class="playlist-name">{{ pl.playlistName }}</div>
                      <div class="playlist-meta">{{ pl.collectCount || 0 }} 收藏</div>
                    </div>
                  </div>
                </div>

                <!-- 推荐歌曲 -->
                <div v-if="recommendMusics.length > 0" class="recommend-section">
                  <h3 class="recommend-title">相似歌曲</h3>
                  <div class="similar-music-list">
                    <div
                      v-for="sm in recommendMusics"
                      :key="sm.id"
                      class="similar-music-item"
                      @click="onPlaySimilar(sm)"
                    >
                      <img
                        v-if="sm.image1Url"
                        :src="sm.image1Url"
                        class="similar-cover"
                        :alt="sm.musicName"
                      />
                      <div v-else class="similar-cover-placeholder">
                        <el-icon><Headset /></el-icon>
                      </div>
                      <div class="similar-info">
                        <div class="similar-name">{{ sm.musicName }}</div>
                        <div class="similar-artist">{{ joinNames(sm.authorNameList) }}</div>
                      </div>
                      <div class="similar-play-count">▶ {{ sm.playCount ?? 0 }}</div>
                    </div>
                  </div>
                </div>

                <!-- 空状态 -->
                <div v-if="recommendPlaylists.length === 0 && recommendMusics.length === 0" class="empty-recommend">
                  <el-icon :size="32"><List /></el-icon>
                  <p>暂无相似推荐</p>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 评论区 -->
      <div class="player-comment-wrapper">
        <CommentSection
          v-if="musicId != null"
          scene-type="music"
          :scene-id="musicId"
        />
      </div>
    </template>
  </div>
</template>

<style scoped src="./player-page.css"></style>
