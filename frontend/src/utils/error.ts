import { isAxiosError } from 'axios'

function extractDetailMessage(data: unknown): string | null {
  if (!data || typeof data !== 'object') return null

  // FastAPI 常用格式：{ detail: string } 或 { detail: [{ msg: string }] }
  if ('detail' in data) {
    const detail = (data as Record<string, unknown>).detail
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first && typeof first === 'object' && 'msg' in first) {
        const msg = (first as Record<string, unknown>).msg
        if (typeof msg === 'string' && msg.trim()) {
          return msg
        }
      }
    }
  }

  // 通用格式：{ message: string }
  if ('message' in data) {
    const msg = (data as Record<string, unknown>).message
    if (typeof msg === 'string' && msg.trim()) {
      return msg
    }
  }

  return null
}

export function parseErrorMessage(
  error: unknown,
  fallback = '操作失败，请稍后重试',
): string {
  if (!isAxiosError(error)) return fallback
  const msg = extractDetailMessage(error.response?.data)
  return msg || fallback
}

export function isAuthError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false
  return (error as Record<string, unknown>).__is_auth_error === true
}
