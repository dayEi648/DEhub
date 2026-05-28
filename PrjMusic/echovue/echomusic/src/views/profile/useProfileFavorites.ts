import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPlayHistoryByUser } from '@/api/playHistory'
import { getPlaylistPage } from '@/api/playlist'
import { getCollectedPlaylists, getCollectedAlbums, uncollectPlaylist, uncollectAlbum } from '@/api/user'
import { getUser } from '@/utils/authStorage'
import type { PlayHistoryVO } from '@/types/playHistory'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'

export interface RecentSong {
  id: number
  name: string
  playedAt: string
  cover: string
  artist: string
  fileUrl: string
}

export interface PlaylistCard {
  id: number
  name: string
  cover: string
  songCount: number
  playCount: string
  isPrivate?: boolean
}

export interface AlbumCard {
  id: number
  name: string
  artist: string
  cover: string
  year: string
}

export function useProfileFavorites() {
  const user = computed(() => getUser())
  const loading = ref(false)

  // 最近听歌
  const recentSongs = ref<RecentSong[]>([])

  // 我的歌单
  const myPlaylists = ref<PlaylistCard[]>([])

  // 收藏歌单
  const collectedPlaylists = ref<PlaylistCard[]>([])

  // 收藏专辑
  const collectedAlbums = ref<AlbumCard[]>([])

  async function loadRecentSongs() {
    if (!user.value?.id) return
    try {
      const list = await getPlayHistoryByUser(user.value.id)
      recentSongs.value = list.slice(0, 6).map((item) => ({
        id: item.songId || Number(item.id),
        name: item.musicName || `歌曲 #${item.songId}`,
        playedAt: formatPlayedAt(item.playedAt),
        cover: item.coverUrl || '',
        artist: '未知作者',
        fileUrl: item.fileUrl || ''
      }))
    } catch {
      // API 失败时使用 mock
      recentSongs.value = [
        { id: 1, name: '夏日终曲', playedAt: '10分钟前', cover: '', artist: '未知作者', fileUrl: '' },
        { id: 2, name: '城市霓虹', playedAt: '2小时前', cover: '', artist: '未知作者', fileUrl: '' },
        { id: 3, name: '远山淡影', playedAt: '昨天', cover: '', artist: '未知作者', fileUrl: '' },
        { id: 4, name: '量子漫步', playedAt: '昨天', cover: '', artist: '未知作者', fileUrl: '' },
        { id: 5, name: '旧书店', playedAt: '3天前', cover: '', artist: '未知作者', fileUrl: '' },
        { id: 6, name: '潮汐锁定', playedAt: '5天前', cover: '', artist: '未知作者', fileUrl: '' }
      ]
    }
  }

  async function loadMyPlaylists() {
    if (!user.value?.id) return
    try {
      const page = await getPlaylistPage({
        pageNum: 1,
        pageSize: 8,
        userId: user.value.id
      })
      myPlaylists.value = page.records.map((pl) => ({
        id: pl.id,
        name: pl.playlistName,
        cover: pl.imageUrl || '',
        songCount: pl.songIds?.length || 0,
        playCount: formatCount(pl.playCount || 0),
        isPrivate: pl.isPrivate ?? false
      }))
    } catch {
      // API 失败时使用 mock
      myPlaylists.value = [
        { id: 1, name: '我喜欢的音乐', cover: '', songCount: 128, playCount: '2.3万' },
        { id: 2, name: '通勤路上', cover: '', songCount: 45, playCount: '8,521' },
        { id: 3, name: '写作背景音', cover: '', songCount: 67, playCount: '1.2万' },
        { id: 4, name: '雨天专属', cover: '', songCount: 32, playCount: '5,430' }
      ]
    }
  }

  function formatPlayedAt(playedAt?: string): string {
    if (!playedAt) return '未知时间'
    const date = new Date(playedAt)
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

  function formatCount(count: number): string {
    if (count >= 10000) {
      return (count / 10000).toFixed(1) + '万'
    }
    return count.toLocaleString()
  }

  async function loadCollectedPlaylists() {
    if (!user.value?.id) return
    try {
      const list = await getCollectedPlaylists()
      collectedPlaylists.value = list.map((pl) => ({
        id: pl.id,
        name: pl.playlistName,
        cover: pl.imageUrl || '',
        songCount: pl.songIds?.length || 0,
        playCount: formatCount(pl.playCount || 0)
      }))
    } catch {
      collectedPlaylists.value = []
    }
  }

  async function loadCollectedAlbums() {
    if (!user.value?.id) return
    try {
      const list = await getCollectedAlbums()
      collectedAlbums.value = list.map((album) => ({
        id: album.id,
        name: album.albumName,
        artist: album.authorNames?.join(' / ') || '未知艺人',
        cover: album.image1Url || '',
        year: album.createTime ? album.createTime.slice(0, 4) : ''
      }))
    } catch {
      collectedAlbums.value = []
    }
  }

  onMounted(() => {
    loading.value = true
    Promise.all([
      loadRecentSongs(),
      loadMyPlaylists(),
      loadCollectedPlaylists(),
      loadCollectedAlbums()
    ]).finally(() => {
      loading.value = false
    })
  })

  async function handleUncollectPlaylist(id: number) {
    try {
      await ElMessageBox.confirm('确定要取消收藏这个歌单吗？', '取消收藏', {
        confirmButtonText: '取消收藏',
        cancelButtonText: '再想想',
        type: 'warning'
      })
      await uncollectPlaylist(id)
      ElMessage.success('已取消收藏')
      loadCollectedPlaylists()
    } catch (err: any) {
      if (err !== 'cancel') {
        ElMessage.error(err.message || '取消收藏失败')
      }
    }
  }

  async function handleUncollectAlbum(id: number) {
    try {
      await ElMessageBox.confirm('确定要取消收藏这个专辑吗？', '取消收藏', {
        confirmButtonText: '取消收藏',
        cancelButtonText: '再想想',
        type: 'warning'
      })
      await uncollectAlbum(id)
      ElMessage.success('已取消收藏')
      loadCollectedAlbums()
    } catch (err: any) {
      if (err !== 'cancel') {
        ElMessage.error(err.message || '取消收藏失败')
      }
    }
  }

  return {
    loading,
    recentSongs,
    myPlaylists,
    collectedPlaylists,
    collectedAlbums,
    loadMyPlaylists,
    loadCollectedPlaylists,
    loadCollectedAlbums,
    handleUncollectPlaylist,
    handleUncollectAlbum,
    formatPlayedAt
  }
}
