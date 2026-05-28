import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getUserById, followUser, unfollowUser } from '@/api/user'
import { getPlayHistoryPage } from '@/api/playHistory'
import { getPlaylistPage } from '@/api/playlist'
import { getMusicPage } from '@/api/music'
import { getAlbumPage } from '@/api/album'
import { getUser } from '@/utils/authStorage'
import { usePlayerStore } from '@/stores/player'
import type { UserVO } from '@/types/user'
import type { PlayHistoryVO } from '@/types/playHistory'
import type { PlaylistVO } from '@/types/playlist'
import type { MusicVO } from '@/types/music'
import type { AlbumVO } from '@/types/album'

export type UserDetailTab = 'profile' | 'space' | 'songs' | 'albums'

export function useUserDetail() {
  const route = useRoute()
  const router = useRouter()
  const playerStore = usePlayerStore()

  const userId = computed(() => Number(route.params.id))
  const currentUser = getUser()

  const user = ref<UserVO | null>(null)
  const userLoading = ref(false)

  const recentSongs = ref<PlayHistoryVO[]>([])
  const recentLoading = ref(false)

  const playlists = ref<PlaylistVO[]>([])
  const playlistLoading = ref(false)

  const songPageData = ref<MusicVO[]>([])
  const songPageNum = ref(1)
  const songPageSize = ref(20)
  const songTotal = ref(0)
  const songLoading = ref(false)

  const albumPageData = ref<AlbumVO[]>([])
  const albumPageNum = ref(1)
  const albumPageSize = ref(12)
  const albumTotal = ref(0)
  const albumLoading = ref(false)

  const activeTab = ref<UserDetailTab>('profile')
  const followLoading = ref(false)

  const isFollowed = computed(() => {
    if (!user.value || !currentUser) return false
    return user.value.fanIds?.includes(currentUser.id) ?? false
  })

  const visibleTabs = computed(() => {
    const base = [
      { key: 'profile' as UserDetailTab, label: '个人资料' },
      { key: 'space' as UserDetailTab, label: '个人空间' }
    ]
    if ((user.value?.songCount ?? 0) > 0) {
      base.push({ key: 'songs' as UserDetailTab, label: '所有单曲' })
      base.push({ key: 'albums' as UserDetailTab, label: '所有专辑' })
    }
    return base
  })

  async function loadUser() {
    const id = userId.value
    if (!id || isNaN(id)) return
    userLoading.value = true
    try {
      user.value = await getUserById(id)
    } catch (err: any) {
      ElMessage.error(err?.msg || '获取用户信息失败')
    } finally {
      userLoading.value = false
    }
  }

  async function loadRecentSongs() {
    const id = userId.value
    if (!id || isNaN(id)) return
    recentLoading.value = true
    try {
      const res = await getPlayHistoryPage(id, 1, 5)
      recentSongs.value = res.records || []
    } catch {
      recentSongs.value = []
    } finally {
      recentLoading.value = false
    }
  }

  async function loadPlaylists() {
    const id = userId.value
    if (!id || isNaN(id)) return
    playlistLoading.value = true
    try {
      const res = await getPlaylistPage({ userId: id, pageNum: 1, pageSize: 200 })
      playlists.value = res.records || []
    } catch {
      playlists.value = []
    } finally {
      playlistLoading.value = false
    }
  }

  async function loadSongs() {
    const id = userId.value
    if (!id || isNaN(id)) return
    songLoading.value = true
    try {
      const res = await getMusicPage({
        authorIds: [id],
        pageNum: songPageNum.value,
        pageSize: songPageSize.value,
        isDeleted: false
      })
      songPageData.value = res.records || []
      songTotal.value = res.total || 0
    } catch {
      songPageData.value = []
      songTotal.value = 0
    } finally {
      songLoading.value = false
    }
  }

  async function loadAlbums() {
    const id = userId.value
    if (!id || isNaN(id)) return
    albumLoading.value = true
    try {
      const res = await getAlbumPage({
        authorIds: [id],
        pageNum: albumPageNum.value,
        pageSize: albumPageSize.value
      })
      albumPageData.value = res.records || []
      albumTotal.value = res.total || 0
    } catch {
      albumPageData.value = []
      albumTotal.value = 0
    } finally {
      albumLoading.value = false
    }
  }

  async function toggleFollow() {
    if (!user.value || !currentUser) {
      ElMessage.info('请先登录')
      return
    }
    if (followLoading.value) return
    followLoading.value = true
    try {
      if (isFollowed.value) {
        await unfollowUser(user.value.id)
        ElMessage.success('已取消关注')
      } else {
        await followUser(user.value.id)
        ElMessage.success('关注成功')
      }
      await loadUser()
    } catch (err: any) {
      ElMessage.error(err?.msg || '操作失败')
    } finally {
      followLoading.value = false
    }
  }

  function onMessage() {
    if (!user.value) return
    if (!currentUser) {
      ElMessage.info('请先登录')
      return
    }
    const key = currentUser.id < user.value.id
      ? `${currentUser.id}:${user.value.id}`
      : `${user.value.id}:${currentUser.id}`
    router.push(`/private-messages/${key}`)
  }

  function playSong(song: MusicVO | PlayHistoryVO) {
    const track = {
      id: (song as any).songId || song.id,
      name: (song as any).musicName || (song as any).name || '未知歌曲',
      artist: ((song as any).authorNameList?.join(' / ') || (song as any).authorNames?.filter(Boolean).join(' / ') || '未知作者'),
      coverUrl: (song as any).image1Url || (song as any).coverUrl || '',
      fileUrl: (song as any).fileUrl || '',
      duration: 0,
      currentTime: 0,
      vip: (song as any).vip
    }
    const ok = playerStore.playTrack(track, true)
    if (!ok) return
  }

  function goPlaylistDetail(id: number) {
    router.push(`/playlist/${id}`)
  }

  function goAlbumDetail(id: number) {
    router.push(`/album/${id}`)
  }

  function goBack() {
    router.back()
  }

  function formatDate(dateStr?: string) {
    if (!dateStr) return '-'
    const d = new Date(dateStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  function genderLabel(gender?: number) {
    switch (gender) {
      case 1: return '男'
      case 2: return '女'
      default: return '未知'
    }
  }

  watch(userId, () => {
    activeTab.value = 'profile'
    songPageNum.value = 1
    albumPageNum.value = 1
    loadUser()
    loadRecentSongs()
    loadPlaylists()
    loadSongs()
    loadAlbums()
  }, { immediate: true })

  watch(activeTab, (tab) => {
    if (tab === 'songs' && songPageData.value.length === 0) {
      loadSongs()
    }
    if (tab === 'albums' && albumPageData.value.length === 0) {
      loadAlbums()
    }
  })

  return {
    user,
    userLoading,
    recentSongs,
    recentLoading,
    playlists,
    playlistLoading,
    songPageData,
    songPageNum,
    songPageSize,
    songTotal,
    songLoading,
    albumPageData,
    albumPageNum,
    albumPageSize,
    albumTotal,
    albumLoading,
    activeTab,
    visibleTabs,
    isFollowed,
    followLoading,
    toggleFollow,
    onMessage,
    playSong,
    goPlaylistDetail,
    goAlbumDetail,
    goBack,
    formatDate,
    genderLabel,
    loadSongs,
    loadAlbums
  }
}
