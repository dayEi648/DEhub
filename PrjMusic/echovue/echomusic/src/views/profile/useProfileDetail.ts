import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getPlayHistoryPage } from '@/api/playHistory'
import { getPlaylistPage, getPlaylistById } from '@/api/playlist'
import { getAlbumById } from '@/api/album'
import { getMusicsByIds } from '@/api/music'
import {
  getCollectedPlaylistsPage,
  getCollectedAlbumsPage,
  uncollectPlaylist,
  uncollectAlbum
} from '@/api/user'
import { getUser } from '@/utils/authStorage'
import { usePlayerStore } from '@/stores/player'
import type { PlayHistoryVO } from '@/types/playHistory'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { MusicVO } from '@/types/music'

export type DetailTab = 'history' | 'playlists' | 'collected-playlists' | 'collected-albums'

export type SongListType = 'playlist' | 'album'

export interface SongListState {
  show: boolean
  type: SongListType
  id: number
  name: string
  songs: MusicVO[]
  pageNum: number
  pageSize: number
  total: number
  loading: boolean
}

const TAB_MAP: Record<string, DetailTab> = {
  '/profile/history': 'history',
  '/profile/playlists': 'playlists',
  '/profile/collected-playlists': 'collected-playlists',
  '/profile/collected-albums': 'collected-albums'
}

const TAB_TITLE: Record<DetailTab, string> = {
  history: '听歌历史',
  playlists: '我的歌单',
  'collected-playlists': '收藏歌单',
  'collected-albums': '收藏专辑'
}

export function useProfileDetail() {
  const route = useRoute()
  const playerStore = usePlayerStore()

  const currentTab = computed<DetailTab>(() => TAB_MAP[route.path] || 'history')
  const pageTitle = computed(() => TAB_TITLE[currentTab.value])

  const loading = ref(false)

  // 听歌历史
  const historyList = ref<PlayHistoryVO[]>([])
  const historyPageNum = ref(1)
  const historyPageSize = ref(10)
  const historyTotal = ref(0)

  // 我的歌单
  const playlistList = ref<PlaylistVO[]>([])
  const playlistPageNum = ref(1)
  const playlistPageSize = ref(12)
  const playlistTotal = ref(0)

  // 收藏歌单
  const collectedPlaylistList = ref<PlaylistVO[]>([])
  const collectedPlaylistPageNum = ref(1)
  const collectedPlaylistPageSize = ref(12)
  const collectedPlaylistTotal = ref(0)

  // 收藏专辑
  const collectedAlbumList = ref<AlbumVO[]>([])
  const collectedAlbumPageNum = ref(1)
  const collectedAlbumPageSize = ref(12)
  const collectedAlbumTotal = ref(0)

  // 歌曲列表视图状态
  const songList = ref<SongListState>({
    show: false,
    type: 'playlist',
    id: 0,
    name: '',
    songs: [],
    pageNum: 1,
    pageSize: 10,
    total: 0,
    loading: false
  })

  // 用户收藏的音乐IDs（用于判断收藏状态）
  const user = computed(() => getUser())
  const localCollectMusicIds = ref<Set<number>>(new Set(user.value?.collectMusicIds || []))
  const collectMusicIds = computed(() => localCollectMusicIds.value)

  // 加载听歌历史
  async function loadHistory() {
    const uid = user.value?.id
    if (!uid) return
    loading.value = true
    try {
      const res = await getPlayHistoryPage(uid, historyPageNum.value, historyPageSize.value)
      historyList.value = res.records
      historyTotal.value = res.total
    } catch {
      ElMessage.error('加载听歌历史失败')
    } finally {
      loading.value = false
    }
  }

  // 加载我的歌单
  async function loadPlaylists() {
    const uid = user.value?.id
    if (!uid) return
    loading.value = true
    try {
      const res = await getPlaylistPage({
        pageNum: playlistPageNum.value,
        pageSize: playlistPageSize.value,
        userId: uid
      })
      playlistList.value = res.records
      playlistTotal.value = res.total
    } catch {
      ElMessage.error('加载我的歌单失败')
    } finally {
      loading.value = false
    }
  }

  // 加载收藏歌单
  async function loadCollectedPlaylists() {
    loading.value = true
    try {
      const res = await getCollectedPlaylistsPage(collectedPlaylistPageNum.value, collectedPlaylistPageSize.value)
      collectedPlaylistList.value = res.records
      collectedPlaylistTotal.value = res.total
    } catch {
      ElMessage.error('加载收藏歌单失败')
    } finally {
      loading.value = false
    }
  }

  // 加载收藏专辑
  async function loadCollectedAlbums() {
    loading.value = true
    try {
      const res = await getCollectedAlbumsPage(collectedAlbumPageNum.value, collectedAlbumPageSize.value)
      collectedAlbumList.value = res.records
      collectedAlbumTotal.value = res.total
    } catch {
      ElMessage.error('加载收藏专辑失败')
    } finally {
      loading.value = false
    }
  }

  // 进入歌曲列表
  async function enterSongList(type: SongListType, id: number, name: string) {
    songList.value.show = true
    songList.value.type = type
    songList.value.id = id
    songList.value.name = name
    songList.value.pageNum = 1
    songList.value.songs = []
    songList.value.total = 0
    songList.value.loading = true

    try {
      let songIds: number[] = []
      if (type === 'playlist') {
        const pl = await getPlaylistById(id)
        songIds = pl.songIds || []
      } else {
        const album = await getAlbumById(id)
        songIds = album.songIds || []
      }
      songList.value.total = songIds.length

      if (songIds.length > 0) {
        const musics = await getMusicsByIds(songIds)
        // 保持与 songIds 一致的顺序
        const musicMap = new Map(musics.map(m => [m.id, m]))
        songList.value.songs = songIds
          .map(sid => musicMap.get(sid))
          .filter((m): m is MusicVO => m != null)
      }
    } catch {
      ElMessage.error('加载歌曲列表失败')
    } finally {
      songList.value.loading = false
    }
  }

  // 返回上一级
  function backFromSongList() {
    songList.value.show = false
    songList.value.songs = []
    songList.value.id = 0
    songList.value.name = ''
  }

  // 歌曲列表分页数据（前端分页）
  const songListPageData = computed(() => {
    const start = (songList.value.pageNum - 1) * songList.value.pageSize
    const end = start + songList.value.pageSize
    return songList.value.songs.slice(start, end)
  })

  // 播放歌曲（将当前歌单/专辑或听歌历史作为播放列表）
  function playMusic(music: MusicVO) {
    if (!music.fileUrl) {
      ElMessage.warning('暂无播放资源')
      return
    }

    let tracks: { id: number; name: string; artist: string; coverUrl: string; fileUrl: string; duration: number; currentTime: number }[] = []
    let startIndex = 0

    if (songList.value.songs.length > 0) {
      // 在歌曲列表视图中，使用 songList 作为播放列表
      tracks = songList.value.songs.map(s => ({
        id: s.id,
        name: s.musicName,
        artist: s.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
        coverUrl: s.image1Url || '',
        fileUrl: s.fileUrl || '',
        duration: 0,
        currentTime: 0
      }))
      startIndex = songList.value.songs.findIndex(s => s.id === music.id)
    } else if (currentTab.value === 'history') {
      // 在听歌历史页面，使用 historyList 作为播放列表
      tracks = historyList.value.map(h => ({
        id: h.songId || 0,
        name: h.musicName || '未知歌曲',
        artist: h.authorNames?.filter(Boolean).join(' / ') || '未知作者',
        coverUrl: h.coverUrl || '',
        fileUrl: h.fileUrl || '',
        duration: 0,
        currentTime: 0
      }))
      startIndex = historyList.value.findIndex(h => h.songId === music.id)
    } else {
      // 其他情况，单首播放
      tracks = [{
        id: music.id,
        name: music.musicName,
        artist: music.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
        coverUrl: music.image1Url || '',
        fileUrl: music.fileUrl || '',
        duration: 0,
        currentTime: 0
      }]
      startIndex = 0
    }

    playerStore.playPlaylist(tracks, startIndex >= 0 ? startIndex : 0)
    playerStore.showBar()
  }

  // 格式化播放时间
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

  // 根据当前 tab 加载数据
  function loadCurrentTab() {
    switch (currentTab.value) {
      case 'history':
        loadHistory()
        break
      case 'playlists':
        loadPlaylists()
        break
      case 'collected-playlists':
        loadCollectedPlaylists()
        break
      case 'collected-albums':
        loadCollectedAlbums()
        break
    }
  }

  // 监听分页变化
  watch([historyPageNum, historyPageSize], loadHistory)
  watch([playlistPageNum, playlistPageSize], loadPlaylists)
  watch([collectedPlaylistPageNum, collectedPlaylistPageSize], loadCollectedPlaylists)
  watch([collectedAlbumPageNum, collectedAlbumPageSize], loadCollectedAlbums)

  // 监听路由变化：切换 tab 时重新加载数据
  watch(() => route.path, (newPath, oldPath) => {
    if (newPath !== oldPath && TAB_MAP[newPath]) {
      // 关闭歌曲列表视图
      songList.value.show = false
      songList.value.songs = []
      // 刷新当前 tab 数据
      loadCurrentTab()
      // 若从收藏页点击歌单跳转过来，自动打开该歌单歌曲
      if (newPath === '/profile/playlists' && route.query.openId) {
        const id = Number(route.query.openId)
        const name = decodeURIComponent(String(route.query.openName || ''))
        enterSongList('playlist', id, name)
      }
    }
  })

  onMounted(() => {
    loadCurrentTab()
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
  }
}
