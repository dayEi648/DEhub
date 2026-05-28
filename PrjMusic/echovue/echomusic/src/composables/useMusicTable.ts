import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '@/stores/player'
import type { MusicVO } from '@/types/music'

export interface UseMusicTableOptions {
  defaultSortBy?: string
  defaultSortOrder?: 'asc' | 'desc'
  pageSize?: number
}

export function useMusicTable(options: UseMusicTableOptions = {}) {
  const router = useRouter()
  const playerStore = usePlayerStore()

  const pageNum = ref(1)
  const pageSize = ref(options.pageSize || 20)
  const sortBy = ref(options.defaultSortBy || 'hot')
  const sortOrder = ref<'asc' | 'desc'>(options.defaultSortOrder || 'desc')

  const addDialogVisible = ref(false)
  const addDialogMusicId = ref(0)

  const sortOptions = [
    { label: '热度', value: 'hot' },
    { label: '收藏数', value: 'collect_count' },
    { label: '播放量', value: 'play_count' },
    { label: '评论数', value: 'comment_count' }
  ]

  function handlePageChange(newPage: number, reload: () => void) {
    pageNum.value = newPage
    reload()
  }

  function handleSortChange(reload: () => void) {
    pageNum.value = 1
    reload()
  }

  function onPlay(item: MusicVO) {
    const ok = playerStore.playTrack({
      id: item.id,
      name: item.musicName,
      artist: item.authorNameList?.filter(Boolean).join(' / ') || '未知作者',
      coverUrl: item.image1Url || '',
      fileUrl: item.fileUrl || '',
      duration: 0,
      currentTime: 0,
      vip: item.vip
    }, true)
    if (!ok) return
    playerStore.showBar()
    router.push(`/music/${item.id}`)
  }

  function openAddDialog(musicId: number) {
    addDialogMusicId.value = musicId
    addDialogVisible.value = true
  }

  function joinNames(names?: string[]) {
    return names?.filter(Boolean).join(' / ') || '未知作者'
  }

  function formatCount(n?: number) {
    if (n == null) return '0'
    if (n >= 10000) return (n / 10000).toFixed(1) + '万'
    return String(n)
  }

  return {
    pageNum,
    pageSize,
    sortBy,
    sortOrder,
    sortOptions,
    addDialogVisible,
    addDialogMusicId,
    handlePageChange,
    handleSortChange,
    onPlay,
    openAddDialog,
    joinNames,
    formatCount
  }
}
