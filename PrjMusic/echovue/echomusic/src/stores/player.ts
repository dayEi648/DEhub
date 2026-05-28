import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { getUser } from '@/utils/authStorage'
import { recordPlayHistory, getPlayHistoryByUser } from '@/api/playHistory'
import type { PlayHistoryVO } from '@/types/playHistory'

export type PlayMode = 'order' | 'random' | 'singleLoop'

export interface Track {
  id: number
  name: string
  artist: string
  coverUrl: string
  fileUrl?: string
  duration: number
  currentTime: number
  vip?: boolean
}

/**
 * 全局音乐播放器状态管理
 */
export const usePlayerStore = defineStore('player', () => {
  // ========== 全局 Audio 实例 ==========
  const audio = new Audio()

  // ========== State ==========
  const currentTrack = ref<Track>({
    id: 1,
    name: '搁浅',
    artist: '周杰伦',
    coverUrl: 'https://p2.music.126.net/UeTuwE7pvjBpypWLudqukA==/109951165343866386.jpg',
    fileUrl: '',
    duration: 236,
    currentTime: 0
  })

  const isPlaying = ref(false)
  const playMode = ref<PlayMode>('order')

  // 播放列表
  const playlist = ref<Track[]>([])
  const currentIndex = ref<number>(-1)
  // 缓存的播放历史（最多50首）
  const historyPlaylist = ref<Track[]>([])
  const isHistoryLoaded = ref(false)

  const VOLUME_KEY = 'echomusic_player_volume'
  const PLAYER_STATE_KEY = 'echomusic_player_state'

  // 恢复上次播放状态
  function restorePlayerState() {
    const raw = localStorage.getItem(PLAYER_STATE_KEY)
    if (!raw) return
    try {
      const state = JSON.parse(raw)
      if (state.track) {
        currentTrack.value = state.track
        if (state.track.fileUrl) {
          audio.src = state.track.fileUrl
          audio.load()
          audio.currentTime = state.track.currentTime || 0
        }
      }
      if (state.playMode && ['order', 'random', 'singleLoop'].includes(state.playMode)) {
        playMode.value = state.playMode
      }
      if (state.playlist && Array.isArray(state.playlist)) {
        playlist.value = state.playlist
      }
      if (typeof state.currentIndex === 'number') {
        currentIndex.value = state.currentIndex
      }
      loadHistoryPlaylist()
    } catch {
      // ignore invalid state
    }
  }

  // 保存播放状态
  function savePlayerState() {
    localStorage.setItem(PLAYER_STATE_KEY, JSON.stringify({
      track: currentTrack.value,
      playMode: playMode.value,
      playlist: playlist.value,
      currentIndex: currentIndex.value
    }))
  }

  restorePlayerState()

  const savedVolume = localStorage.getItem(VOLUME_KEY)
  const volume = ref(savedVolume ? Math.max(0, Math.min(1, parseFloat(savedVolume))) : 0.7)

  const isMuted = ref(false)
  const isLiked = ref(false)
  const isBarVisible = ref(false)

  refreshLikeStatus()

  // ========== Getters ==========
  const formattedCurrentTime = computed(() => formatTime(currentTrack.value.currentTime))
  const formattedDuration = computed(() => formatTime(currentTrack.value.duration))
  const progressPercent = computed(() => {
    if (currentTrack.value.duration <= 0) return 0
    return (currentTrack.value.currentTime / currentTrack.value.duration) * 100
  })

  // ========== Audio 事件监听 ==========
  audio.addEventListener('loadedmetadata', () => {
    currentTrack.value.duration = audio.duration || 0
  })

  audio.addEventListener('timeupdate', () => {
    currentTrack.value.currentTime = audio.currentTime || 0
  })

  audio.addEventListener('play', () => {
    isPlaying.value = true
  })

  audio.addEventListener('pause', () => {
    isPlaying.value = false
  })

  audio.addEventListener('ended', () => {
    if (playMode.value === 'singleLoop') {
      audio.currentTime = 0
      audio.play().catch(() => {})
    } else {
      nextTrack()
    }
  })

  audio.addEventListener('error', () => {
    isPlaying.value = false
  })

  // 同步音量
  watch(volume, (v) => {
    audio.volume = v
    localStorage.setItem(VOLUME_KEY, v.toString())
  }, { immediate: true })

  // 同步静音
  watch(isMuted, (m) => {
    audio.muted = m
  }, { immediate: true })

  // ========== 播放历史相关 ==========

  function historyVOToTrack(vo: PlayHistoryVO): Track {
    return {
      id: vo.songId || 0,
      name: vo.musicName || '未知歌曲',
      artist: vo.authorNames?.filter(Boolean).join(' / ') || '未知作者',
      coverUrl: vo.coverUrl || '',
      fileUrl: vo.fileUrl || '',
      duration: 0,
      currentTime: 0
    }
  }

  async function loadHistoryPlaylist() {
    const user = getUser()
    if (!user?.id || isHistoryLoaded.value) return
    try {
      const history = await getPlayHistoryByUser(user.id)
      historyPlaylist.value = history
        .filter(h => h.songId && h.fileUrl)
        .map(historyVOToTrack)
        .slice(0, 50)
      isHistoryLoaded.value = true
    } catch {
      // ignore
    }
  }

  function updateHistoryCache(track: Track) {
    if (!track.id) return
    const idx = historyPlaylist.value.findIndex(t => t.id === track.id)
    if (idx >= 0) {
      historyPlaylist.value.splice(idx, 1)
    }
    historyPlaylist.value.unshift({ ...track })
    if (historyPlaylist.value.length > 50) {
      historyPlaylist.value = historyPlaylist.value.slice(0, 50)
    }
  }

  // ========== VIP 权限检查 ==========

  function canPlayVipTrack(track: Track): boolean {
    if (!track.vip) return true
    const user = getUser()
    const role = user?.role ?? 0
    if (role >= 1) return true
    ElMessageBox.alert('该歌曲为VIP专属，请先开通VIP', '提示', {
      confirmButtonText: '知道了',
      type: 'warning'
    })
    return false
  }

  // ========== 核心播放逻辑 ==========

  function doPlay(track: Track) {
    if (!canPlayVipTrack(track)) {
      return
    }
    currentTrack.value = {
      ...track,
      duration: track.duration || 0,
      currentTime: 0
    }

    if (track.fileUrl) {
      audio.src = track.fileUrl
      audio.load()
      audio.play().catch((err) => {
        console.error('播放失败:', err)
        isPlaying.value = false
      })
    } else {
      isPlaying.value = true
    }

    // 记录播放历史（登录状态下）
    const user = getUser()
    if (user?.id) {
      recordPlayHistory({ userId: user.id, songId: track.id }).catch(() => {})
    }

    savePlayerState()
    refreshLikeStatus()
  }

  /**
   * 根据当前用户收藏列表刷新收藏按钮状态
   */
  function refreshLikeStatus() {
    const user = getUser()
    if (!user || !currentTrack.value.id) {
      isLiked.value = false
      return
    }
    isLiked.value = user.collectMusicIds?.includes(currentTrack.value.id) ?? false
  }

  /**
   * 播放指定播放列表中的指定歌曲
   * @param tracks 播放列表
   * @param startIndex 开始播放的索引
   */
  function playPlaylist(tracks: Track[], startIndex: number = 0) {
    if (!tracks.length) return
    const idx = Math.max(0, Math.min(startIndex, tracks.length - 1))
    playlist.value = [...tracks]
    currentIndex.value = idx
    updateHistoryCache(tracks[idx]!)
    doPlay(tracks[idx]!)
  }

  /**
   * 播放指定歌曲（单曲播放时自动关联播放历史作为播放列表）
   * @param track 歌曲信息
   * @param forceRestart 是否强制重新加载（外部点击播放时传 true）
   */
  function playTrack(track: Track, forceRestart = false): boolean {
    if (!canPlayVipTrack(track)) {
      return false
    }
    if (track.id === currentTrack.value.id && !forceRestart) {
      // 同一首歌，只是确保在播放
      if (audio.paused) {
        audio.play().catch(() => {})
      }
      return true
    }

    // 单曲播放：playlist = 当前歌曲 + 播放历史
    const setupHistoryPlaylist = () => {
      updateHistoryCache(track)
      playlist.value = [...historyPlaylist.value]
      currentIndex.value = historyPlaylist.value.findIndex(t => t.id === track.id)
      if (currentIndex.value < 0) currentIndex.value = 0
    }

    if (isHistoryLoaded.value) {
      setupHistoryPlaylist()
    } else {
      // 历史未加载时先设单首，保证立即可播放
      playlist.value = [{ ...track }]
      currentIndex.value = 0
      const user = getUser()
      if (user?.id) {
        loadHistoryPlaylist().then(setupHistoryPlaylist).catch(() => {})
      }
    }

    doPlay(track)
    return true
  }

  /** 播放 */
  function play() {
    if (!audio.src) return
    audio.play().catch(() => {})
  }

  /** 暂停 */
  function pause() {
    audio.pause()
  }

  /** 播放/暂停切换 */
  function togglePlay() {
    if (!audio.src) return
    if (audio.paused) {
      audio.play().catch(() => {})
    } else {
      audio.pause()
    }
  }

  /** 上一首 */
  function prevTrack() {
    if (playlist.value.length === 0) {
      if (audio.src) {
        audio.currentTime = 0
      }
      return
    }

    if (playMode.value === 'singleLoop') {
      audio.currentTime = 0
      audio.play().catch(() => {})
      return
    }

    const newIndex = currentIndex.value > 0 ? currentIndex.value - 1 : playlist.value.length - 1
    currentIndex.value = newIndex
    doPlay(playlist.value[newIndex]!)
  }

  /** 下一首 */
  function nextTrack() {
    if (playlist.value.length === 0) {
      if (audio.src) {
        audio.currentTime = 0
      }
      return
    }

    if (playMode.value === 'singleLoop') {
      audio.currentTime = 0
      audio.play().catch(() => {})
      return
    }

    let newIndex: number
    if (playMode.value === 'random') {
      newIndex = Math.floor(Math.random() * playlist.value.length)
    } else {
      newIndex = currentIndex.value < playlist.value.length - 1 ? currentIndex.value + 1 : 0
    }
    currentIndex.value = newIndex
    doPlay(playlist.value[newIndex]!)
  }

  /** 切换播放模式：顺序 → 随机 → 单曲循环 */
  function togglePlayMode() {
    const modes: PlayMode[] = ['order', 'random', 'singleLoop']
    const idx = modes.indexOf(playMode.value)
    const nextMode = modes[(idx + 1) % modes.length]
    if (nextMode) {
      playMode.value = nextMode
    }
  }

  /** 设置音量 */
  function setVolume(vol: number) {
    volume.value = Math.max(0, Math.min(1, vol))
    if (volume.value > 0 && isMuted.value) {
      isMuted.value = false
    }
  }

  /** 静音切换 */
  function toggleMute() {
    isMuted.value = !isMuted.value
  }

  /** 收藏切换 */
  function toggleLike() {
    isLiked.value = !isLiked.value
  }

  /** 显示底边栏 */
  function showBar() {
    isBarVisible.value = true
  }

  /** 隐藏底边栏 */
  function hideBar() {
    isBarVisible.value = false
  }

  /** 设置播放进度 */
  function seek(time: number) {
    if (!audio.src) return
    const maxTime = currentTrack.value.duration || audio.duration || 0
    const t = Math.max(0, Math.min(maxTime, time))
    audio.currentTime = t
    currentTrack.value.currentTime = t
    savePlayerState()
  }

  /** 格式化时间 mm:ss */
  function formatTime(seconds: number): string {
    const m = Math.floor(seconds / 60)
    const s = Math.floor(seconds % 60)
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  // 页面关闭前保存最终状态
  window.addEventListener('beforeunload', () => {
    savePlayerState()
  })

  return {
    currentTrack,
    isPlaying,
    playMode,
    volume,
    isMuted,
    isLiked,
    isBarVisible,
    playlist,
    currentIndex,
    formattedCurrentTime,
    formattedDuration,
    progressPercent,
    playTrack,
    playPlaylist,
    play,
    pause,
    togglePlay,
    prevTrack,
    nextTrack,
    togglePlayMode,
    setVolume,
    toggleMute,
    toggleLike,
    refreshLikeStatus,
    showBar,
    hideBar,
    seek
  }
})
