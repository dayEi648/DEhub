import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMusicById, getRecommendMusics } from '@/api/music'
import { getRecommendPlaylists } from '@/api/playlist'
import type { MusicVO } from '@/types/music'
import type { PlaylistVO } from '@/types/playlist'
import { usePlayerStore } from '@/stores/player'

export type TabType = 'lyrics' | 'details' | 'similar'

export function usePlayerPage() {
  const route = useRoute()
  const router = useRouter()

  const musicId = computed(() => Number(route.params.id))

  // 音乐详情
  const music = ref<MusicVO | null>(null)
  const loading = ref(false)
  const error = ref('')

  // Tab
  const activeTab = ref<TabType>('lyrics')

  // 相似推荐
  const recommendPlaylists = ref<PlaylistVO[]>([])
  const recommendMusics = ref<MusicVO[]>([])
  const recommendLoading = ref(false)

  // 加载音乐详情
  async function loadMusic() {
    const id = musicId.value
    if (!id || isNaN(id)) {
      error.value = '无效的音乐ID'
      return
    }
    loading.value = true
    error.value = ''
    try {
      music.value = await getMusicById(id)
      await loadRecommendations()
    } catch (e: any) {
      error.value = e?.message || '加载失败'
      ElMessage.error('音乐加载失败')
    } finally {
      loading.value = false
    }
  }

  // 加载相似推荐
  async function loadRecommendations() {
    const id = musicId.value
    if (!id) return
    recommendLoading.value = true
    try {
      const [pls, musics] = await Promise.all([
        getRecommendPlaylists(id).catch(() => []),
        getRecommendMusics(id).catch(() => [])
      ])
      recommendPlaylists.value = pls.filter(pl => !pl.isPrivate && !pl.isLike && pl.isRecommended === true)
      recommendMusics.value = musics
    } finally {
      recommendLoading.value = false
    }
  }

  // 返回上一页
  function goBack() {
    router.back()
  }

  // 跳转到其他音乐播放页
  function goToMusic(id: number) {
    router.push(`/music/${id}`)
  }

  // 监听ID变化，重新加载
  watch(musicId, () => {
    activeTab.value = 'lyrics'
    loadMusic()
  }, { immediate: true })

  // 监听当前播放歌曲变化，自动跳转跟随
  const playerStore = usePlayerStore()
  watch(() => playerStore.currentTrack?.id, (newId) => {
    if (newId && newId !== musicId.value) {
      router.replace(`/music/${newId}`)
    }
  })

  return {
    music,
    loading,
    error,
    activeTab,
    recommendPlaylists,
    recommendMusics,
    recommendLoading,
    loadMusic,
    loadRecommendations,
    goBack,
    goToMusic
  }
}
