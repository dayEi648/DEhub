import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Token refresh state
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function getToken(): string | null {
  return localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
}

function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token')
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
  sessionStorage.removeItem('access_token')
  sessionStorage.removeItem('refresh_token')
  sessionStorage.removeItem('user')
}

// Request interceptor
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 当 data 为 FormData 时，删除全局默认的 Content-Type，
    // 让浏览器自动设置 multipart/form-data（包含正确的 boundary）
    if (config.data instanceof FormData && config.headers) {
      delete (config.headers as Record<string, unknown>)['Content-Type']
    }
    const uiStore = useUiStore()
    if (!(config as any).skipGlobalLoading) {
      uiStore.setLoading(true)
    }
    return config
  },
  (error) => {
    const uiStore = useUiStore()
    if (!(error.config as any)?.skipGlobalLoading) {
      uiStore.setLoading(false)
    }
    return Promise.reject(error)
  }
)

// Response interceptor
client.interceptors.response.use(
  (response) => {
    const uiStore = useUiStore()
    if (!(response.config as any)?.skipGlobalLoading) {
      uiStore.setLoading(false)
    }
    return response
  },
  async (error: AxiosError<import('@/types').ApiError>) => {
    const uiStore = useUiStore()
    if (!(error.config as any)?.skipGlobalLoading) {
      uiStore.setLoading(false)
    }

    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearTokens()
        const authStore = useAuthStore()
        authStore.clearAuth()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            resolve(client(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post('/api/v1/users/refresh-token', {
          refresh_token: refreshToken
        })
        const data = response.data as import('@/types').UserLoginResponse
        const newAccessToken = data.access_token
        const newRefreshToken = data.refresh_token

        if (localStorage.getItem('refresh_token')) {
          localStorage.setItem('access_token', newAccessToken)
          if (newRefreshToken) localStorage.setItem('refresh_token', newRefreshToken)
        } else {
          sessionStorage.setItem('access_token', newAccessToken)
          if (newRefreshToken) sessionStorage.setItem('refresh_token', newRefreshToken)
        }

        const authStore = useAuthStore()
        authStore.setAccessToken(newAccessToken)
        if (newRefreshToken) authStore.setRefreshToken(newRefreshToken)

        onRefreshed(newAccessToken)
        isRefreshing = false

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        }
        return client(originalRequest)
      } catch (refreshError) {
        isRefreshing = false
        clearTokens()
        const authStore = useAuthStore()
        authStore.clearAuth()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default client
