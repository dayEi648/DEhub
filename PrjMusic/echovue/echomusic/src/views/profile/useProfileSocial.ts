import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getFollowsPage, getFansPage, followUser, unfollowUser } from '@/api/user'
import { getUser } from '@/utils/authStorage'
import type { UserVO } from '@/types/user'

export type SocialSubTab = 'follows' | 'fans'

export function useProfileSocial() {
  const router = useRouter()
  const currentUser = getUser()

  const activeSubTab = ref<SocialSubTab>('follows')
  const users = ref<UserVO[]>([])
  const pageNum = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const loading = ref(false)

  const isFollowed = (user: UserVO): boolean => {
    if (!currentUser) return false
    return user.fanIds?.includes(currentUser.id) ?? false
  }

  async function loadData() {
    if (!currentUser) {
      ElMessage.info('请先登录')
      return
    }
    loading.value = true
    try {
      let res
      if (activeSubTab.value === 'follows') {
        res = await getFollowsPage(pageNum.value, pageSize.value)
      } else {
        res = await getFansPage(pageNum.value, pageSize.value)
      }
      users.value = res.records || []
      total.value = res.total || 0
    } catch (err: any) {
      ElMessage.error(err?.msg || '加载失败')
    } finally {
      loading.value = false
    }
  }

  async function toggleFollow(user: UserVO) {
    if (!currentUser) {
      ElMessage.info('请先登录')
      return
    }
    try {
      if (isFollowed(user)) {
        await unfollowUser(user.id)
        ElMessage.success('已取消关注')
      } else {
        await followUser(user.id)
        ElMessage.success('关注成功')
      }
      await loadData()
    } catch (err: any) {
      ElMessage.error(err?.msg || '操作失败')
    }
  }

  function goUserDetail(id: number) {
    router.push(`/user/${id}`)
  }

  function handlePageChange() {
    loadData()
  }

  watch(activeSubTab, () => {
    pageNum.value = 1
    loadData()
  }, { immediate: true })

  return {
    activeSubTab,
    users,
    pageNum,
    pageSize,
    total,
    loading,
    isFollowed,
    loadData,
    toggleFollow,
    goUserDetail,
    handlePageChange
  }
}
