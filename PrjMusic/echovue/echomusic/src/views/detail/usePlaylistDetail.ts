import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPlaylistById } from '@/api/playlist'
import { getAlbumById } from '@/api/album'
import { getMusicsByIds } from '@/api/music'
import {
  getCollectedPlaylists,
  getCollectedAlbums,
  collectPlaylist,
  uncollectPlaylist,
  collectAlbum,
  uncollectAlbum
} from '@/api/user'
import { getUser } from '@/utils/authStorage'
import { usePlayerStore } from '@/stores/player'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { MusicVO } from '@/types/music'
import type { Track } from '@/stores/player'

export type DetailType = 'playlist' | 'album'

export function usePlaylistDetail() {
  const route = useRoute()
  const router = useRouter()
  const playerStore = usePlayerStore()

  const type = computed<DetailType>(() => {
    const path = route.path
    if (path.startsWith('/playlist')) return 'playlist'
    return 'album'
  })

  const id = computed(() => Number(route.params.id))

  // 详情数据
  const playlist = ref<PlaylistVO | null>(null)
  const album = ref<AlbumVO | null>(null)
  const detailLoading = ref(false)

  // 歌曲列表
  const songs = ref<MusicVO[]>([])
  const songPageNum = ref(1)
  const songPageSize = ref(10)
  const songLoading = ref(false)

  // 收藏状态
  const isCollected = ref(false)
  const collectLoading = ref(false)

  // 详情标题
  const detailName = computed(() => {
    if (type.value === 'playlist') return playlist.value?.playlistName || ''
    return album.value?.albumName || ''
  })

  // 封面
  const coverUrl = computed(() => {
    if (type.value === 'playlist') return playlist.value?.imageUrl || ''
    return album.value?.image1Url || ''
  })

  // 创建者/作者
  const creatorText = computed(() => {
    if (type.value === 'playlist') {
      return playlist.value?.userName || '未知用户'
    }
    return album.value?.authorNames?.filter(Boolean).join(' / ') || '未知作者'
  })

  // 是否为自己的歌单
  const isOwnPlaylist = computed(() => {
    const user = getUser()
    if (!user || type.value !== 'playlist') return false
    return playlist.value?.userId === user.id
  })

  // 描述
  const description = computed(() => {
    if (type.value === 'playlist') return playlist.value?.listDescription || ''
    return album.value?.albumDescription || ''
  })

  // 统计数据
  const playCount = computed(() => {
    if (type.value === 'playlist') return playlist.value?.playCount ?? 0
    return album.value?.playCount ?? 0
  })

  const collectCount = computed(() => {
    if (type.value === 'playlist') return playlist.value?.collectCount ?? 0
    return album.value?.collectCount ?? 0
  })

  const hot = computed(() => {
    if (type.value === 'playlist') return playlist.value?.hot ?? 0
    return album.value?.hot ?? 0
  })

  // 头部评论数（album 不支持评论）
  const headerCommentCount = computed(() => {
    if (type.value === 'playlist') return playlist.value?.commentCount ?? 0
    return 0
  })

  // 歌曲列表分页数据
  const songPageData = computed(() => {
    const start = (songPageNum.value - 1) * songPageSize.value
    const end = start + songPageSize.value
    return songs.value.slice(start, end)
  })

  const songTotal = computed(() => songs.value.length)

  // 格式化数字
  function formatCount(n: number): string {
    if (n >= 10000) return (n / 10000).toFixed(1) + '万'
    return String(n)
  }

  // 加载详情
  async function loadDetail() {
    const currentId = id.value
    if (!currentId || isNaN(currentId)) return

    detailLoading.value = true
    try {
      let songIds: number[] = []
      if (type.value === 'playlist') {
        const pl = await getPlaylistById(currentId)
        playlist.value = pl
        album.value = null
        songIds = pl.songIds || []
      } else {
        const al = await getAlbumById(currentId)
        album.value = al
        playlist.value = null
        songIds = al.songIds || []
      }
      // 并行加载歌曲、收藏状态
      await Promise.all([
        loadSongsByIds(songIds),
        checkCollectStatus()
      ])
    } catch {
      ElMessage.error('加载详情失败')
    } finally {
      detailLoading.value = false
    }
  }

  // 根据 IDs 加载歌曲
  async function loadSongsByIds(songIds: number[]) {
    songLoading.value = true
    try {
      if (songIds.length > 0) {
        const musics = await getMusicsByIds(songIds)
        const musicMap = new Map(musics.map(m => [m.id, m]))
        songs.value = songIds
          .map(sid => musicMap.get(sid))
          .filter((m): m is MusicVO => m != null)
      } else {
        songs.value = []
      }
      songPageNum.value = 1
    } catch {
      ElMessage.error('加载歌曲列表失败')
      songs.value = []
    } finally {
      songLoading.value = false
    }
  }

  function musicVOToTrack(music: MusicVO): Track {
    return {
      id: music.id,
      name: music.musicName,
      artist: music.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
      coverUrl: music.image1Url || '',
      fileUrl: music.fileUrl || '',
      duration: 0,
      currentTime: 0
    }
  }

  // 检查收藏状态
  async function checkCollectStatus() {
    const currentId = id.value
    if (!currentId || isNaN(currentId)) {
      isCollected.value = false
      return
    }
    try {
      if (type.value === 'playlist') {
        const list = await getCollectedPlaylists()
        isCollected.value = list.some(item => item.id === currentId)
      } else {
        const list = await getCollectedAlbums()
        isCollected.value = list.some(item => item.id === currentId)
      }
    } catch {
      isCollected.value = false
    }
  }

  // 切换收藏
  async function toggleCollect() {
    const currentId = id.value
    if (!currentId || isNaN(currentId)) return

    if (type.value === 'playlist' && isOwnPlaylist.value) {
      ElMessage.warning('不能收藏自己的歌单')
      return
    }

    const user = getUser()
    if (!user) {
      ElMessage.warning('请先登录')
      return
    }

    if (isCollected.value) {
      // 取消收藏：弹出确认框
      try {
        await ElMessageBox.confirm('是否取消收藏？', '提示', {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        })
      } catch {
        return // 用户取消
      }

      collectLoading.value = true
      try {
        if (type.value === 'playlist') {
          await uncollectPlaylist(currentId)
        } else {
          await uncollectAlbum(currentId)
        }
        isCollected.value = false
        // 更新本地收藏数
        if (type.value === 'playlist' && playlist.value) {
          playlist.value.collectCount = (playlist.value.collectCount ?? 1) - 1
        } else if (album.value) {
          album.value.collectCount = (album.value.collectCount ?? 1) - 1
        }
        ElMessage.success('已取消收藏')
      } catch {
        ElMessage.error('操作失败')
      } finally {
        collectLoading.value = false
      }
    } else {
      // 添加收藏
      collectLoading.value = true
      try {
        if (type.value === 'playlist') {
          await collectPlaylist(currentId)
        } else {
          await collectAlbum(currentId)
        }
        isCollected.value = true
        // 更新本地收藏数
        if (type.value === 'playlist' && playlist.value) {
          playlist.value.collectCount = (playlist.value.collectCount ?? 0) + 1
        } else if (album.value) {
          album.value.collectCount = (album.value.collectCount ?? 0) + 1
        }
        ElMessage.success('收藏成功')
      } catch {
        ElMessage.error('操作失败')
      } finally {
        collectLoading.value = false
      }
    }
  }

  // 播放歌曲（将整个歌单/专辑作为播放列表）
  function playMusic(music: MusicVO) {
    if (!music.fileUrl) {
      ElMessage.warning('暂无播放资源')
      return
    }
    const tracks = songs.value.map(musicVOToTrack)
    const index = songs.value.findIndex(s => s.id === music.id)
    playerStore.playPlaylist(tracks, index >= 0 ? index : 0)
    playerStore.showBar()
  }

  // 返回上一页
  function goBack() {
    router.back()
  }

  // 格式化时间
  function formatTime(time?: string): string {
    if (!time) return ''
    const date = new Date(time)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days === 1) return '昨天'
    if (days < 7) return `${days}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }

  // 监听路由参数变化
  watch([type, id], () => {
    if (id.value && !isNaN(id.value)) {
      songPageNum.value = 1
      loadDetail()
    }
  }, { immediate: true })

  return {
    type,
    id,
    playlist,
    album,
    detailLoading,
    songs,
    songPageData,
    songPageNum,
    songPageSize,
    songTotal,
    songLoading,
    isCollected,
    collectLoading,
    isOwnPlaylist,
    detailName,
    coverUrl,
    creatorText,
    description,
    playCount,
    collectCount,
    hot,
    headerCommentCount,
    formatCount,
    loadDetail,
    loadSongsByIds,
    toggleCollect,
    playMusic,
    goBack,
    formatTime
  }
}
