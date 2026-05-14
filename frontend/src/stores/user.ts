import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserResponse } from '@/types'
import * as userApi from '@/api/user'
import { useAuthStore } from './auth'
import { useUiStore } from './ui'

export const useUserStore = defineStore('user', () => {
  const authStore = useAuthStore()
  const uiStore = useUiStore()

  const currentUser = ref<UserResponse | null>(null)
  const userList = ref<UserResponse[]>([])
  const totalUsers = ref(0)

  async function fetchCurrentUser() {
    if (authStore.user) {
      currentUser.value = authStore.user
    }
  }

  async function updateProfile(id: number, data: Partial<UserResponse> & { password?: string }, file?: File) {
    const formData = new FormData()
    // FastAPI multipart 中 Pydantic 模型通过同名字段传递 JSON 字符串
    formData.append('user_in', JSON.stringify(data))
    if (file) formData.append('file', file)
    const { data: updated } = await userApi.updateUser(id, formData)
    authStore.user = updated
    currentUser.value = updated
    uiStore.showToast('保存成功', 'success')
    return updated
  }

  async function fetchUsers(params?: Parameters<typeof userApi.fetchUsers>[0]) {
    const { data } = await userApi.fetchUsers(params)
    userList.value = data.items
    totalUsers.value = data.total
    return data
  }

  async function deleteUser(id: number) {
    await userApi.deleteUser(id)
    userList.value = userList.value.filter((u) => u.id !== id)
    uiStore.showToast('用户已注销', 'success')
  }

  async function hardDeleteUser(id: number) {
    await userApi.hardDeleteUser(id)
    userList.value = userList.value.filter((u) => u.id !== id)
    uiStore.showToast('用户已彻底删除', 'success')
  }

  async function createUser(data: import('@/types').UserCreate) {
    const { data: userData } = await userApi.createUser(data)
    userList.value.unshift(userData)
    totalUsers.value += 1
    return userData
  }

  async function changePassword(data: { old_password: string; new_password: string }) {
    await userApi.changePassword(data)
    uiStore.showToast('密码修改成功，请重新登录', 'success')
    // 修改密码后所有 Token 自动失效，执行登出
    await authStore.logout()
  }

  return {
    currentUser,
    userList,
    totalUsers,
    fetchCurrentUser,
    updateProfile,
    fetchUsers,
    deleteUser,
    hardDeleteUser,
    createUser,
    changePassword
  }
})
