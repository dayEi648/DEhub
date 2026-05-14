export interface SSEOptions {
  method?: string
  headers?: Record<string, string>
  body?: string
  onMessage: (data: string) => void
  onError?: (error: any) => void
  onDone?: () => void
}

export function fetchSSE(url: string, options: SSEOptions) {
  const controller = new AbortController()

  fetch(url, {
    method: options.method || 'GET',
    headers: options.headers || {},
    body: options.body,
    signal: controller.signal
  }).then(async (response) => {
    if (!response.body) {
      options.onError?.(new Error('No response body'))
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('event: error')) {
            options.onError?.(new Error('SSE error event'))
            return
          }
          if (trimmed.startsWith('data: ')) {
            const data = trimmed.slice(6)
            if (data === '[DONE]') {
              options.onDone?.()
              return
            }
            options.onMessage(data)
          }
        }
      }
      options.onDone?.()
    } catch (err) {
      options.onError?.(err)
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      options.onError?.(err)
    }
  })

  return {
    abort: () => controller.abort()
  }
}
