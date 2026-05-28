import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { logout as logoutApi } from '@/api/user'
import { getUser, clearAuth } from '@/utils/authStorage'
import { getBanners } from '@/api/banner'
import { getMusicById, getHomeHotMusics, getHomeNewMusics } from '@/api/music'
import { getHomeRecommendPlaylists } from '@/api/playlist'
import { usePlayerStore } from '@/stores/player'
import type { UserVO } from '@/types/user'
import type { BannerVO } from '@/types/banner'
import type { PlaylistVO } from '@/types/playlist'
import type { MusicVO } from '@/types/music'

export interface PlaylistItem {
  id: number
  name: string
  playCount: string
  tag: string
  coverUrl?: string
}

export interface SongItem {
  id: number
  name: string
  artist: string
  duration: string
  isNew?: boolean
  coverUrl?: string
  fileUrl?: string
  hot?: number
  hotLevel?: number
  trend?: string
}

function formatPlayCount(count: number | undefined): string {
  if (count == null) return '0'
  if (count >= 10000) {
    return (count / 10000).toFixed(1).replace(/\.0$/, '') + '万'
  }
  return String(count)
}

export function useHomePage() {
  const router = useRouter()
  const playerStore = usePlayerStore()
  const user = ref<UserVO | null>(getUser())
  const searchKeyword = ref('')

  // 轮播图数据
  const carouselList = ref<BannerVO[]>([])
  const bannersLoading = ref(false)

  // 推荐歌单数据
  const playlistList = ref<PlaylistItem[]>([])

  // 热门音乐数据
  const hotSongs = ref<SongItem[]>([])

  // 新歌速递数据
  const newSongs = ref<SongItem[]>([])

  const displayName = computed(() => {
    return user.value?.name || user.value?.username || '用户'
  })

  const userLevel = computed(() => {
    return user.value?.level || 1
  })

  const avatarUrl = computed(() => {
    return user.value?.avatar || 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
  })

  function handleSearch() {
    const kw = searchKeyword.value.trim()
    if (!kw) {
      ElMessage.info('请输入搜索关键词')
      return
    }
    router.push({ path: '/search', query: { keyword: kw, type: 'all' } })
  }

  function goToAdmin() {
    router.push('/users')
  }

  function goToProfile() {
    router.push('/profile')
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

  async function loadBanners() {
    bannersLoading.value = true
    try {
      carouselList.value = await getBanners()
    } catch {
      carouselList.value = []
    } finally {
      bannersLoading.value = false
    }
  }

  async function loadHomeRecommend() {
    try {
      const data: PlaylistVO[] = await getHomeRecommendPlaylists()
      playlistList.value = data.map((pl: PlaylistVO) => ({
        id: pl.id,
        name: pl.playlistName,
        playCount: formatPlayCount(pl.playCount),
        tag: pl.emoTags?.[0] || pl.interestTags?.[0] || '推荐',
        coverUrl: pl.imageUrl
      }))
    } catch {
      playlistList.value = []
    }
  }

  async function loadHomeHot() {
    try {
      const data: MusicVO[] = await getHomeHotMusics()
      hotSongs.value = data.map((m: MusicVO) => ({
        id: m.id,
        name: m.musicName,
        artist: m.authorNameList?.join('/') || '未知作者',
        duration: '',
        coverUrl: m.image1Url || m.image2Url || m.image3Url || '',
        fileUrl: m.fileUrl || '',
        hot: m.hot,
        hotLevel: m.hotLevel,
        trend: m.trend
      }))
    } catch {
      hotSongs.value = []
    }
  }

  async function loadHomeNew() {
    try {
      const data: MusicVO[] = await getHomeNewMusics()
      newSongs.value = data.map((m: MusicVO) => ({
        id: m.id,
        name: m.musicName,
        artist: m.authorNameList?.join('/') || '未知作者',
        duration: '',
        isNew: true,
        coverUrl: m.image1Url || m.image2Url || m.image3Url || '',
        fileUrl: m.fileUrl || ''
      }))
    } catch {
      newSongs.value = []
    }
  }

  async function handleBannerClick(banner: BannerVO) {
    if (banner.targetType === 'MUSIC') {
      try {
        const music = await getMusicById(banner.targetId)
        if (music) {
          const ok = playerStore.playTrack({
            id: music.id,
            name: music.musicName,
            artist: music.authorIds?.length ? `作者${music.authorIds.join('/')}` : '未知作者',
            coverUrl: music.image1Url || music.image2Url || music.image3Url || '',
            fileUrl: music.fileUrl || '',
            duration: 0,
            currentTime: 0,
            vip: music.vip
          }, true)
          if (!ok) return
          router.push(`/music/${banner.targetId}`)
        }
      } catch {
        ElMessage.error('音乐加载失败')
      }
    } else if (banner.targetType === 'ALBUM') {
      router.push(`/album/${banner.targetId}`)
    }
  }

  function handlePlaySong(song: SongItem) {
    if (!song.fileUrl) {
      // 尝试从后端获取完整音乐信息再播放
      getMusicById(song.id)
        .then((music) => {
          if (music.fileUrl) {
            const ok = playerStore.playTrack({
              id: music.id,
              name: music.musicName,
              artist: music.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
              coverUrl: music.image1Url || music.image2Url || music.image3Url || '',
              fileUrl: music.fileUrl,
              duration: 0,
              currentTime: 0,
              vip: music.vip
            }, true)
            if (!ok) return
            playerStore.showBar()
            router.push(`/music/${song.id}`)
          } else {
            ElMessage.warning('暂无播放资源')
          }
        })
        .catch(() => {
          ElMessage.error('音乐加载失败')
        })
      return
    }

    const ok = playerStore.playTrack({
      id: song.id,
      name: song.name,
      artist: song.artist,
      coverUrl: song.coverUrl || '',
      fileUrl: song.fileUrl,
      duration: 0,
      currentTime: 0,
      vip: (song as any).vip
    }, true)
    if (!ok) return
    playerStore.showBar()
    router.push(`/music/${song.id}`)
  }

  function handlePlaylistClick(pl: PlaylistItem) {
    router.push(`/playlist/${pl.id}`)
  }

  onMounted(() => {
    loadBanners()
    loadHomeRecommend()
    loadHomeHot()
    loadHomeNew()
  })

  return {
    user,
    searchKeyword,
    carouselList,
    bannersLoading,
    playlistList,
    hotSongs,
    newSongs,
    displayName,
    userLevel,
    avatarUrl,
    handleSearch,
    goToAdmin,
    goToProfile,
    handleLogout,
    handleBannerClick,
    handlePlaySong,
    handlePlaylistClick
  }
}
