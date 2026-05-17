import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { UserResponse, UserLoginResponse, UserLogin, UserCreate } from '@/types'
import * as authApi from '@/api/auth'
import { useUiStore } from './ui'

export const useAuthStore = defineStore('auth', () => {
  const uiStore = useUiStore()

  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const tokenType = ref<string>('Bearer')
  const user = ref<UserResponse | null>(null)
  const expiresAt = ref<number | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin = computed(() => user.value ? user.value.permission >= 1 : false)
  const isSuperAdmin = computed(() => user.value ? user.value.permission >= 2 : false)

  function setAccessToken(token: string) {
    accessToken.value = token
  }

  function setRefreshToken(token: string) {
    refreshToken.value = token
  }

  function clearAuth() {
    accessToken.value = null
    refreshToken.value = null
    tokenType.value = 'Bearer'
    user.value = null
    expiresAt.value = null
  }

  function persistSession(data: UserLoginResponse, remember: boolean = false) {
    const storage = remember ? localStorage : sessionStorage
    storage.setItem('access_token', data.access_token)
    if (data.refresh_token) storage.setItem('refresh_token', data.refresh_token)
    storage.setItem('user', JSON.stringify(data.user))

    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user
    if (data.access_token_expires_in) {
      expiresAt.value = Date.now() + data.access_token_expires_in * 60 * 1000
    }
  }

  async function login(credentials: UserLogin) {
    const { data } = await authApi.login(credentials)
    persistSession(data, credentials.is_remember)
    uiStore.showToast('登录成功', 'success')
    return data.user
  }

  async function register(data: UserCreate) {
    const { data: userData } = await authApi.register(data)
    uiStore.showToast('注册成功', 'success')
    return userData
  }

  function clearStorage() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')
    sessionStorage.removeItem('user')
  }

  async function logout() {
    try {
      await authApi.logout(refreshToken.value || undefined)
    } catch {
      // ignore
    }
    clearStorage()
    clearAuth()
    uiStore.showToast('已登出', 'success')
    window.location.href = '/login'
  }

  async function refreshTokenAction() {
    const rt = refreshToken.value || localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token')
    if (!rt) throw new Error('No refresh token')
    const { data } = await authApi.refreshToken(rt)
    persistSession(data, !!localStorage.getItem('refresh_token'))
    return data.access_token
  }

  async function restoreSession() {
    const at = localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    const rt = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token')
    const userJson = localStorage.getItem('user') || sessionStorage.getItem('user')

    if (userJson) {
      try {
        user.value = JSON.parse(userJson) as UserResponse
      } catch {
        user.value = null
      }
    }

    // 优先恢复 accessToken，避免 refresh 网络波动导致无辜登出
    if (at) {
      accessToken.value = at
    }

    if (rt) {
      refreshToken.value = rt
      try {
        const { data } = await authApi.refreshToken(rt)
        persistSession(data, !!localStorage.getItem('refresh_token'))
      } catch {
        // refresh 失败不强制清除已有状态；后续 API 返回 401 时由拦截器处理
      }
    }
  }

  return {
    accessToken,
    refreshToken,
    tokenType,
    user,
    expiresAt,
    isAuthenticated,
    isAdmin,
    isSuperAdmin,
    setAccessToken,
    setRefreshToken,
    clearAuth,
    login,
    register,
    logout,
    refreshTokenAction,
    restoreSession
  }
})
