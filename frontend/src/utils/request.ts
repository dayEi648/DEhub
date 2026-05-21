import axios from 'axios'
import { clearAuth } from './auth'

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

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth()
      window.location.href = '/login'
    } else if (error.response?.data?.message) {
      alert(`请求失败：${error.response.data.message}`)
    } else {
      alert('网络错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default request
