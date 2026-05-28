import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig
} from 'axios'


import { ElMessage } from 'element-plus'
import { getToken, clearAuth } from '@/utils/authStorage'

/**
 * 统一响应结构
 */
interface Result<T> {
  code: number
  msg: string
  data: T
}

/**
 * Spring MVC 绑定 List 查询参数需要重复键名：ids=1&ids=2（单值 ids=1,2 常无法绑定为 List）。
 */
function springQuerySerialize(params: Record<string, unknown>): string {
  const sp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null) {
          sp.append(key, String(item))
        }
      })
    } else {
      sp.append(key, String(value))
    }
  }
  return sp.toString()
}

/**
 * 创建axios实例
 */
const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  },
  paramsSerializer: {
    serialize: springQuerySerialize
  }
})

/**
 * 请求拦截器
 */
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getToken()
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`)
    }
    if (config.data instanceof FormData) {
      config.headers.delete('Content-Type')
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 */
request.interceptors.response.use(
  (response: AxiosResponse<Result<any>>) => {
    const { data } = response

    // 业务成功
    if (data.code === 200) {
      return response
    }

    // 业务失败
    ElMessage.error(data.msg || '操作失败')
    return Promise.reject(new Error(data.msg || '操作失败'))
  },
  (error) => {
    // 网络或服务器错误
    let message = '网络错误，请稍后重试'

    if (error.response) {
      const { status } = error.response
      switch (status) {
        case 400:
          message = '请求参数错误'
          break
        case 401:
          message = '未登录或登录已过期'
          clearAuth()
          window.location.href = '/login'
          break
        case 403:
          message = '没有权限执行此操作'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = `请求失败: ${status}`
      }
    } else if (error.request) {
      message = '无法连接到服务器，请检查网络'
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/**
 * GET请求
 */
export function get<T>(url: string, params?: object): Promise<T> {
  return request.get(url, { params }).then((res) => res.data.data)
}

/**
 * POST请求
 */
export function post<T>(url: string, data?: object): Promise<T> {
  return request.post(url, data).then((res) => res.data.data)
}

/**
 * PUT请求
 */
export function put<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
  return request.put(url, data, config).then((res) => res.data.data)
}

/**
 * DELETE请求
 */
export function del<T>(url: string, params?: object): Promise<T> {
  return request.delete(url, { params }).then((res) => res.data.data)
}

/**
 * POST multipart/form-data (e.g. OSS file upload). Interceptor clears Content-Type so the boundary is set automatically.
 */
export function postForm<T>(url: string, data: FormData): Promise<T> {
  return request.post(url, data).then((res) => res.data.data)
}

/**
 * PUT multipart/form-data
 */
export function putForm<T>(url: string, data: FormData): Promise<T> {
  return request.put(url, data).then((res) => res.data.data)
}

export default request
