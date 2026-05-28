import { get, post, del, postForm } from '@/utils/request'
import { getToken, clearAuth } from '@/utils/authStorage'
import type {
  AiSession,
  AiMessage,
  ChatRequest,
  ChatResponse,
  SseCallbacks
} from '@/types/aiAgent'

/**
 * 非流式 AI 对话
 */
export function chat(data: ChatRequest): Promise<ChatResponse> {
  return post('/ai/chat', data)
}

/**
 * 流式 AI 对话（SSE，使用 fetch + ReadableStream 手动解析）
 */
export async function chatStream(
  data: ChatRequest,
  callbacks: SseCallbacks
): Promise<void> {
  const token = getToken()
  if (!token) {
    callbacks.onError?.('未登录，请先登录')
    return
  }

  let response: Response
  try {
    response = await fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    })
  } catch (e) {
    callbacks.onError?.('网络错误，无法连接到 AI 服务')
    return
  }

  if (!response.ok) {
    let msg = `请求失败: ${response.status}`
    try {
      const err = await response.json()
      msg = err.msg || msg
    } catch {
      /* ignore */
    }
    if (response.status === 401) {
      clearAuth()
      window.location.href = '/login'
      return
    }
    if (response.status === 429) {
      callbacks.onError?.('当前会话正在处理中，请稍后再试')
      return
    }
    callbacks.onError?.(msg)
    return
  }

  if (!response.body) {
    callbacks.onError?.('浏览器不支持流式响应')
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = 'message'
  let currentData = ''
  let hasData = false

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event:')) {
          // 遇到新 event，先 flush 上一个
          if (hasData) {
            dispatchSseEvent(currentEvent, currentData, callbacks)
            currentData = ''
            hasData = false
          }
          currentEvent = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          currentData = line.slice(5).trim()
          hasData = true
        } else if (line === '' && hasData) {
          dispatchSseEvent(currentEvent, currentData, callbacks)
          currentData = ''
          hasData = false
        }
      }
    }

    // 处理剩余 buffer
    if (buffer.trim()) {
      const line = buffer.trim()
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        dispatchSseEvent(currentEvent, line.slice(5).trim(), callbacks)
      }
    }
    if (hasData) {
      dispatchSseEvent(currentEvent, currentData, callbacks)
    }
  } catch (e) {
    callbacks.onError?.('读取流式响应时出错')
  } finally {
    reader.releaseLock()
  }
}

function dispatchSseEvent(event: string, data: string, callbacks: SseCallbacks) {
  try {
    const parsed = JSON.parse(data)
    switch (event) {
      case 'tool_end':
        callbacks.onToolEnd?.(parsed)
        break
      case 'message_delta':
        callbacks.onMessageDelta?.(parsed.content || '')
        break
      case 'done':
        callbacks.onDone?.(parsed)
        break
      case 'error':
        callbacks.onError?.(parsed.msg || '流式响应错误')
        break
      default:
        // 未知 event 类型，尝试作为消息增量处理
        if (parsed.content) {
          callbacks.onMessageDelta?.(parsed.content)
        }
    }
  } catch {
    // 非 JSON，直接作为文本增量
    callbacks.onMessageDelta?.(data)
  }
}

/**
 * 获取会话列表
 */
export function getSessions(): Promise<AiSession[]> {
  return get('/ai/sessions')
}

/**
 * 分页获取会话消息
 */
export function getMessages(
  sessionId: string,
  pageNum: number = 1,
  pageSize: number = 20
): Promise<AiMessage[]> {
  return get(`/ai/sessions/${sessionId}/messages`, { pageNum, pageSize })
}

/**
 * 会话心跳
 */
export function heartbeat(sessionId: string): Promise<void> {
  return post(`/ai/sessions/${sessionId}/heartbeat`)
}

/**
 * 删除会话
 */
export function deleteSession(sessionId: string): Promise<void> {
  return del(`/ai/sessions/${sessionId}`)
}

// ==================== 知识库管理（管理员） ====================

/**
 * 上传知识库文档
 */
export function uploadKnowledge(file: File): Promise<void> {
  const fd = new FormData()
  fd.append('file', file)
  return postForm('/ai/knowledge', fd)
}

/**
 * 查询知识库文档列表
 */
export function getKnowledgePage(
  pageNum: number = 1,
  pageSize: number = 20
): Promise<{ total: number; records: any[] }> {
  return get('/ai/knowledge', { pageNum, pageSize })
}

/**
 * 删除知识库文档
 */
export function deleteKnowledgeDoc(docId: string): Promise<void> {
  return del(`/ai/knowledge/${docId}`)
}

/**
 * 创建新会话
 */
export function createSession(): Promise<{ session_id: string }> {
  return post('/ai/sessions')
}

/**
 * 清理会话 Redis 缓存
 */
export function clearMemory(sessionId: string): Promise<void> {
  return del(`/ai/sessions/${sessionId}/memory`)
}
