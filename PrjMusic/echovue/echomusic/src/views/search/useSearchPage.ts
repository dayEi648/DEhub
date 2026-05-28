import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  searchAll,
  searchMusics,
  searchPlaylists,
  searchAlbums,
  searchSingers,
  searchUsers
} from '@/api/search'
import type { MusicVO, PageDataVo } from '@/types/music'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { UserVO } from '@/types/user'

export type SearchTab = 'all' | 'musics' | 'playlists' | 'albums' | 'singers' | 'users'

interface TabState<T> {
  records: T[]
  total: number
  pageNum: number
  pageSize: number
}

export function useSearchPage() {
  const route = useRoute()
  const router = useRouter()

  const keyword = ref('')
  const activeTab = ref<SearchTab>('all')
  const loading = ref(false)

  const allData = ref<{
    musics: MusicVO[]
    playlists: PlaylistVO[]
    albums: AlbumVO[]
    singers: UserVO[]
  }>({
    musics: [],
    playlists: [],
    albums: [],
    singers: []
  })

  const musicState = ref<TabState<MusicVO>>({ records: [], total: 0, pageNum: 1, pageSize: 20 })
  const playlistState = ref<TabState<PlaylistVO>>({ records: [], total: 0, pageNum: 1, pageSize: 20 })
  const albumState = ref<TabState<AlbumVO>>({ records: [], total: 0, pageNum: 1, pageSize: 20 })
  const singerState = ref<TabState<UserVO>>({ records: [], total: 0, pageNum: 1, pageSize: 20 })
  const userState = ref<TabState<UserVO>>({ records: [], total: 0, pageNum: 1, pageSize: 20 })

  function initFromRoute() {
    const q = (route.query.keyword as string) || ''
    const t = (route.query.type as SearchTab) || 'all'
    keyword.value = q
    activeTab.value = t
  }

  function switchTab(tab: SearchTab) {
    activeTab.value = tab
    router.replace({
      path: '/search',
      query: { keyword: keyword.value, type: tab }
    })
  }

  function doSearch() {
    const k = keyword.value.trim()
    if (!k) {
      ElMessage.info('请输入搜索关键词')
      return
    }
    router.replace({
      path: '/search',
      query: { keyword: k, type: activeTab.value }
    })
  }

  async function fetchAll() {
    const k = keyword.value.trim()
    if (!k) return
    loading.value = true
    try {
      const res = await searchAll(k)
      allData.value.musics = res.musics || []
      allData.value.playlists = res.playlists || []
      allData.value.albums = res.albums || []
      allData.value.singers = res.singers || []
    } finally {
      loading.value = false
    }
  }

  async function fetchTabData(tab: SearchTab) {
    const k = keyword.value.trim()
    if (!k || tab === 'all') return
    loading.value = true
    try {
      let res: PageDataVo<any> | undefined
      switch (tab) {
        case 'musics':
          res = await searchMusics(k, musicState.value.pageNum, musicState.value.pageSize)
          break
        case 'playlists':
          res = await searchPlaylists(k, playlistState.value.pageNum, playlistState.value.pageSize)
          break
        case 'albums':
          res = await searchAlbums(k, albumState.value.pageNum, albumState.value.pageSize)
          break
        case 'singers':
          res = await searchSingers(k, singerState.value.pageNum, singerState.value.pageSize)
          break
        case 'users':
          res = await searchUsers(k, userState.value.pageNum, userState.value.pageSize)
          break
      }
      if (res) {
        const state = getState(tab)
        state.records = res.records || []
        state.total = res.total || 0
      }
    } finally {
      loading.value = false
    }
  }

  function getState(tab: SearchTab): TabState<any> {
    switch (tab) {
      case 'musics': return musicState.value
      case 'playlists': return playlistState.value
      case 'albums': return albumState.value
      case 'singers': return singerState.value
      case 'users': return userState.value
      default: return musicState.value
    }
  }

  function handlePageChange(tab: SearchTab, page: number) {
    const state = getState(tab)
    state.pageNum = page
    fetchTabData(tab)
  }

  function goUserDetail(id: number) {
    router.push(`/user/${id}`)
  }

  watch(
    () => route.query,
    () => {
      initFromRoute()
      if (activeTab.value === 'all') {
        fetchAll()
      } else {
        fetchTabData(activeTab.value)
      }
    },
    { immediate: true }
  )

  return {
    keyword,
    activeTab,
    loading,
    allData,
    musicState,
    playlistState,
    albumState,
    singerState,
    userState,
    switchTab,
    doSearch,
    handlePageChange,
    goUserDetail
  }
}
