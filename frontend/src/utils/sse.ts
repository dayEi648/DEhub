export interface SSEOptions {
  method?: string
  headers?: Record<string, string>
  body?: string
  onMessage: (data: string) => void
  onError?: (error: any) => void
  onDone?: () => void
  onEvent?: (eventType: string, data: string) => void
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

        // SSE events are separated by double newlines
        const eventChunks = buffer.split('\n\n')
        // The last chunk may be incomplete, keep it in buffer
        buffer = eventChunks.pop() || ''

        for (const chunk of eventChunks) {
          if (!chunk.trim()) continue

          const lines = chunk.split('\n')
          let eventType = 'message'
          let data = ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (trimmed.startsWith('event:')) {
              eventType = trimmed.slice(6).trim()
            } else if (trimmed.startsWith('data:')) {
              // Append multiple data lines with newlines
              if (data) data += '\n'
              data += trimmed.slice(5).trimStart()
            }
          }

          if (eventType === 'error') {
            let errorMessage = 'SSE error event'
            try {
              const parsed = JSON.parse(data)
              errorMessage = parsed.message || errorMessage
            } catch {
              if (data) errorMessage = data
            }
            options.onError?.(new Error(errorMessage))
            return
          }

          if (eventType !== 'message') {
            options.onEvent?.(eventType, data)
            continue
          }

          if (data === '[DONE]') {
            options.onDone?.()
            return
          }

          if (data) {
            options.onMessage(data)
          }
        }
      }

      // Handle any remaining complete event in buffer
      if (buffer.trim()) {
        const lines = buffer.split('\n')
        let eventType = 'message'
        let data = ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('event:')) {
            eventType = trimmed.slice(6).trim()
          } else if (trimmed.startsWith('data:')) {
            if (data) data += '\n'
            data += trimmed.slice(5).trimStart()
          }
        }

        if (eventType === 'error') {
          let errorMessage = 'SSE error event'
          try {
            const parsed = JSON.parse(data)
            errorMessage = parsed.message || errorMessage
          } catch {
            if (data) errorMessage = data
          }
          options.onError?.(new Error(errorMessage))
          return
        }

        if (eventType !== 'message') {
          options.onEvent?.(eventType, data)
          return
        }

        if (data === '[DONE]') {
          options.onDone?.()
          return
        }

        if (data) {
          options.onMessage(data)
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
