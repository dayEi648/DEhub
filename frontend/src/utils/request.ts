import axios from 'axios'
import { toast } from 'sonner'
import { clearAuth, getRefreshToken, setToken, setRefreshToken, setUser, isTokenExpired } from './auth'
import { refreshToken } from '../api/users'
import { parseErrorMessage } from './error'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []
let lastAuthToastAt = 0

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function showAuthToast() {
  const now = Date.now()
  if (now - lastAuthToastAt > 3000) {
    lastAuthToastAt = now
    toast.info('请先登录')
  }
}

function markAuthError(error: unknown): void {
  if (error && typeof error === 'object') {
    ;(error as Record<string, unknown>).__is_auth_error = true
  }
}

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    if (isTokenExpired()) {
      const err = new Error('Token 已过期') as unknown as Record<string, unknown>
      err.__is_auth_error = true
      return Promise.reject(err)
    }
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 统一认证错误处理（含请求拦截器前置拦截的 __is_auth_error）
    const isAuthError = error.__is_auth_error === true || error.response?.status === 401

    if (isAuthError && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true

      const rt = getRefreshToken()
      // 仅当为响应 401 且存在 refresh token 时才尝试刷新
      if (error.response?.status === 401 && rt) {
        if (!isRefreshing) {
          isRefreshing = true
          try {
            const res = await refreshToken({ refresh_token: rt })
            const newToken = res.data.access_token
            setToken(newToken)
            if (res.data.refresh_token) {
              setRefreshToken(res.data.refresh_token)
            }
            setUser(res.data.user)
            onRefreshed(newToken)
            isRefreshing = false
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return request(originalRequest)
          } catch {
            isRefreshing = false
            refreshSubscribers = []
          }
        } else {
          // 正在刷新中，排队等待
          return new Promise((resolve) => {
            addRefreshSubscriber((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(request(originalRequest))
            })
          })
        }
      }

      // 刷新失败、无 refresh token、或前置拦截的过期 token：统一清理并提示
      clearAuth()
      showAuthToast()
      window.dispatchEvent(new CustomEvent('unauthorized'))
      markAuthError(error)
      return Promise.reject(error)
    }

    // 非认证错误，显示后端返回的详细错误信息
    const msg = parseErrorMessage(error, '请求失败，请稍后重试')
    if (msg) {
      toast.error(msg)
    }
    return Promise.reject(error)
  },
)

export default request
