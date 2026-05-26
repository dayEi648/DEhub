import axios from 'axios'
import { clearAuth, getRefreshToken, setToken, setRefreshToken, setUser } from './auth'
import { refreshToken } from '../api/users'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

request.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // 401 时尝试刷新 token
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      const rt = getRefreshToken()
      if (rt) {
        originalRequest._retry = true

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
            clearAuth()
            window.dispatchEvent(new CustomEvent('unauthorized'))
            return Promise.reject(error)
          }
        }

        // 正在刷新中，排队等待
        return new Promise((resolve) => {
          addRefreshSubscriber((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }

      clearAuth()
      window.dispatchEvent(new CustomEvent('unauthorized'))
      return Promise.reject(error)
    }

    // 非 401 错误，静默处理（不再 alert 阻塞用户）
    return Promise.reject(error)
  },
)

export default request
