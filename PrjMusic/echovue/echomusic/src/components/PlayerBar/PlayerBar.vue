<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Star, StarFilled } from '@element-plus/icons-vue'
import { usePlayerStore } from '@/stores/player'
import { getUser, setUser } from '@/utils/authStorage'
import AddToPlaylistDialog from '@/views/profile/AddToPlaylistDialog.vue'

const store = usePlayerStore()
const route = useRoute()
const router = useRouter()

const isAuthPage = computed(() => route.path === '/login' || route.path === '/register')

// 唤起 / 隐藏计时器
let hideTimer: ReturnType<typeof setTimeout> | null = null

function onMouseEnter() {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  store.showBar()
}

function onMouseLeave() {
  hideTimer = setTimeout(() => {
    store.hideBar()
  }, 3000)
}

// 进度条绑定（0-100）
const progressValue = computed({
  get: () => store.progressPercent,
  set: (val: number) => {
    const time = (val / 100) * store.currentTrack.duration
    store.seek(time)
  }
})

// 音量绑定（0-100）
const volumeValue = computed({
  get: () => Math.round(store.volume * 100),
  set: (val: number) => store.setVolume(val / 100)
})

// 播放顺序按钮 tooltip
const modeLabels: Record<string, string> = {
  order: '列表循环',
  random: '随机播放',
  singleLoop: '单曲循环'
}
const modeTooltip = computed(() => modeLabels[store.playMode])

// 收藏 tooltip
const likeTooltip = computed(() => store.isLiked ? '取消收藏' : '收藏')

// 添加到歌单弹窗
const addDialogVisible = ref(false)
const addDialogMusicId = ref(0)

function openAddToPlaylistDialog() {
  addDialogMusicId.value = store.currentTrack.id
  addDialogVisible.value = true
}

function onAddToPlaylist() {
  addDialogVisible.value = false
  store.isLiked = true
  // 同步更新 localStorage 中的 collectMusicIds
  const user = getUser()
  if (user && store.currentTrack.id) {
    const ids = new Set(user.collectMusicIds ?? [])
    ids.add(store.currentTrack.id)
    user.collectMusicIds = Array.from(ids)
    setUser(user)
  }
}
</script>

<template>
  <div
    v-if="!isAuthPage"
    class="player-bar"
    :class="{ visible: store.isBarVisible }"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
  >
    <!-- 常驻触发条 -->
    <div class="trigger-bar"></div>

    <!-- 主面板 -->
    <div class="panel-inner">
      <!-- 左侧：歌曲信息 -->
      <div class="section-left">
        <img
          :src="store.currentTrack.coverUrl"
          class="track-cover"
          alt="cover"
          @click="router.push(`/music/${store.currentTrack.id}`)"
        />
        <div class="track-info">
          <div class="track-name" :title="store.currentTrack.name">
            {{ store.currentTrack.name }}
          </div>
          <div class="track-artist">{{ store.currentTrack.artist }}</div>
        </div>
        <el-tooltip :content="likeTooltip" placement="top" :show-after="300">
          <button class="icon-btn like-btn" @click="openAddToPlaylistDialog">
            <el-icon :size="18">
              <StarFilled v-if="store.isLiked" />
              <Star v-else />
            </el-icon>
          </button>
        </el-tooltip>
      </div>

      <!-- 中间：播放控制 -->
      <div class="section-center">
        <div class="control-btns">
          <!-- 上一首 -->
          <button class="icon-btn ctrl-btn" @click="store.prevTrack">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <rect x="4" y="5" width="3" height="14" rx="0.5"/>
              <path d="M20 5L10 12l10 7V5z"/>
            </svg>
          </button>

          <!-- 播放 / 暂停 -->
          <button class="play-btn" @click="store.togglePlay">
            <svg v-if="!store.isPlaying" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M8 5.14v13.72a1 1 0 001.5.86l11-6.86a1 1 0 000-1.72l-11-6.86a1 1 0 00-1.5.86z"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <rect x="6" y="4" width="4" height="16" rx="1"/>
              <rect x="14" y="4" width="4" height="16" rx="1"/>
            </svg>
          </button>

          <!-- 下一首 -->
          <button class="icon-btn ctrl-btn" @click="store.nextTrack">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M4 5l10 7-10 7V5z"/>
              <rect x="17" y="5" width="3" height="14" rx="0.5"/>
            </svg>
          </button>
        </div>

        <div class="progress-row">
          <span class="time-text">{{ store.formattedCurrentTime }}</span>
          <el-slider
            v-model="progressValue"
            :max="100"
            :show-tooltip="false"
            size="small"
            class="progress-slider"
          />
          <span class="time-text">{{ store.formattedDuration }}</span>
        </div>
      </div>

      <!-- 右侧：附加控制 -->
      <div class="section-right">
        <!-- 播放顺序 -->
        <el-tooltip :content="modeTooltip" placement="top" :show-after="300">
          <button class="icon-btn mode-btn" @click="store.togglePlayMode">
            <!-- 顺序播放 -->
            <svg v-if="store.playMode === 'order'" viewBox="0 0 20 20" width="16" height="16" fill="currentColor">
              <path d="M2 5h10v1H2zm0 4h8v1H2zm0 4h9v1H2z"/>
              <path d="M14 3l4 3.5L14 10"/>
            </svg>
            <!-- 随机播放 -->
            <svg v-else-if="store.playMode === 'random'" viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
              <path d="M3 3l14 14M17 3L3 17"/>
            </svg>
            <!-- 单曲循环 -->
            <svg v-else viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round">
              <path d="M13 2l3 3.5-3 3.5"/>
              <path d="M3 9V7a3 3 0 013-3h10"/>
              <path d="M7 18l-3-3.5 3-3.5"/>
              <path d="M16 11v2a3 3 0 01-3 3H3"/>
              <text x="10" y="12" text-anchor="middle" font-size="7" fill="currentColor" stroke="none" font-weight="bold">1</text>
            </svg>
          </button>
        </el-tooltip>

        <!-- 音量 -->
        <div class="volume-group">
          <button class="icon-btn volume-btn" @click="store.toggleMute">
            <svg v-if="store.isMuted || store.volume === 0" viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M11 5L6 9H2v6h4l5 4V5z"/>
              <path d="M23 9l-6 6M17 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M11 5L6 9H2v6h4l5 4V5z"/>
              <path d="M15.54 8.46a5 5 0 010 7.07M19.07 4.93a10 10 0 010 14.14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>
            </svg>
          </button>
          <el-slider
            v-model="volumeValue"
            :max="100"
            :show-tooltip="false"
            size="small"
            class="volume-slider"
          />
        </div>
      </div>
    </div>
  </div>

  <AddToPlaylistDialog
    :visible="addDialogVisible"
    :music-id="addDialogMusicId"
    @submit="onAddToPlaylist"
    @cancel="addDialogVisible = false"
  />
</template>

<style scoped>
/* ========== 外层容器 ========== */
.player-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9990;
  transform: translateY(72px);
  transition: transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: auto;
}

.player-bar.visible {
  transform: translateY(0);
}

/* ========== 触发条 ========== */
.trigger-bar {
  height: 4px;
  background: rgba(107, 70, 193, 0.3);
  transition: background 0.3s ease;
  cursor: pointer;
}

.player-bar:hover .trigger-bar {
  background: rgba(107, 70, 193, 0.6);
}

.player-bar.visible .trigger-bar {
  background: transparent;
}

/* ========== 主面板 ========== */
.panel-inner {
  height: 72px;
  background: rgba(20, 18, 30, 0.88);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  padding: 0 24px;
  gap: 24px;
}

/* ========== 通用按钮 ========== */
.icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.icon-btn:hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.08);
}

.icon-btn:active {
  transform: scale(0.92);
}

/* ========== 左侧：歌曲信息 ========== */
.section-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 0 0 auto;
  max-width: 220px;
}

.track-cover {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.track-cover:hover {
  transform: scale(1.08);
  box-shadow: 0 4px 12px rgba(107, 70, 193, 0.3);
}

.track-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  overflow: hidden;
}

.track-name {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.track-artist {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}

.like-btn {
  color: #94a3b8;
}

.like-btn:hover {
  color: #ec4899;
  background: rgba(236, 72, 153, 0.1);
}

.like-btn .el-icon {
  transition: transform 0.2s ease;
}

.like-btn:active .el-icon {
  transform: scale(1.3);
}

/* ========== 中间：播放控制 ========== */
.section-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.control-btns {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ctrl-btn {
  width: 32px;
  height: 32px;
  color: #cbd5e1;
}

.ctrl-btn:hover {
  color: #fff;
}

.play-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 50%;
  background: #6b46c1;
  color: #fff;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(107, 70, 193, 0.35);
}

.play-btn:hover {
  background: #7c4ddb;
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(107, 70, 193, 0.5);
}

.play-btn:active {
  transform: scale(0.95);
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: 480px;
}

.time-text {
  font-size: 11px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
  flex-shrink: 0;
  min-width: 36px;
  text-align: center;
}

.progress-slider {
  flex: 1;
}

/* ========== 右侧：附加控制 ========== */
.section-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 0 0 auto;
  max-width: 220px;
  justify-content: flex-end;
}

.mode-btn {
  color: #94a3b8;
}

.mode-btn:hover {
  color: #e2e8f0;
}

.volume-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.volume-btn {
  color: #94a3b8;
}

.volume-btn:hover {
  color: #e2e8f0;
}

.volume-slider {
  width: 80px;
}

/* ========== Element Plus Slider 自定义 ========== */
.player-bar :deep(.el-slider__runway) {
  background: rgba(255, 255, 255, 0.08);
  height: 3px;
  border-radius: 2px;
  margin: 8px 0;
}

.player-bar :deep(.el-slider__bar) {
  background: #6b46c1;
  border-radius: 2px;
}

.player-bar :deep(.el-slider__button) {
  width: 10px;
  height: 10px;
  border: 2px solid #fff;
  background: #6b46c1;
  opacity: 0;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.player-bar :deep(.el-slider:hover .el-slider__button) {
  opacity: 1;
}

.player-bar :deep(.el-slider__button:hover) {
  transform: scale(1.3);
}

.player-bar :deep(.el-slider__button-wrapper) {
  top: -10px;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .panel-inner {
    padding: 0 12px;
    gap: 12px;
  }

  .section-left {
    max-width: 140px;
  }

  .track-info {
    display: none;
  }

  .section-right {
    max-width: 120px;
  }

  .volume-slider {
    width: 50px;
  }

  .progress-row {
    max-width: 100%;
  }
}
</style>
