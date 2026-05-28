import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export type DiscoverTab =
  | 'overview'
  | 'hot'
  | 'new'
  | 'vip'
  | 'playlist'
  | 'album'
  | 'emotion'
  | 'interest'
  | 'style'
  | 'instrument'
  | 'language'

const TAB_LIST: { key: DiscoverTab; label: string }[] = [
  { key: 'overview', label: '综合' },
  { key: 'hot', label: '热歌榜' },
  { key: 'new', label: '新歌榜' },
  { key: 'vip', label: 'VIP' },
  { key: 'playlist', label: '歌单' },
  { key: 'album', label: '专辑' },
  { key: 'emotion', label: '情绪' },
  { key: 'interest', label: '兴趣' },
  { key: 'style', label: '曲风' },
  { key: 'instrument', label: '乐器' },
  { key: 'language', label: '语种' }
]

export function useDiscoverPage() {
  const route = useRoute()
  const router = useRouter()

  const activeTab = computed<DiscoverTab>(() => {
    const tab = route.query.tab as string
    const validTabs: DiscoverTab[] = [
      'hot', 'new', 'vip', 'playlist', 'album',
      'emotion', 'interest', 'style', 'instrument', 'language'
    ]
    return validTabs.includes(tab as DiscoverTab) ? (tab as DiscoverTab) : 'overview'
  })

  const searchKeyword = ref('')

  function switchTab(tab: DiscoverTab) {
    if (tab === 'overview') {
      router.replace({ path: '/discover' })
    } else {
      router.replace({ path: '/discover', query: { tab } })
    }
  }

  function handleSearch() {
    const kw = searchKeyword.value.trim()
    if (!kw) return
    router.push({ path: '/search', query: { keyword: kw, type: 'all' } })
  }

  function goToTab(tab: DiscoverTab) {
    switchTab(tab)
  }

  return {
    activeTab,
    searchKeyword,
    tabList: TAB_LIST,
    switchTab,
    handleSearch,
    goToTab
  }
}
