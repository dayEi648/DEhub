import { isAxiosError } from 'axios'

export function parseErrorMessage(
  error: unknown,
  fallback = '操作失败，请稍后重试',
): string {
  if (!isAxiosError(error)) return fallback
  const data = error.response?.data
  if (data && typeof data === 'object' && 'message' in data) {
    const maybeMessage = data.message
    if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
      return maybeMessage
    }
  }
  return fallback
}
