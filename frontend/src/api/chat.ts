import client from './client'
import { fetchSSE } from '@/utils/sse'
import type { ConversationListResponse, MessageResponse, ChatCreate } from '@/types'

export function fetchConversations(params?: { skip?: number; limit?: number }) {
  return client.get<ConversationListResponse>('/chat/conversations', { params })
}

export function fetchMessages(conversationId: number, params?: { skip?: number; limit?: number }) {
  return client.get<MessageResponse[]>(`/chat/conversations/${conversationId}/messages`, { params })
}

export function deleteConversation(id: number) {
  return client.delete(`/chat/conversations/${id}`)
}

export function sendStreamMessage(
  params: ChatCreate,
  callbacks: {
    onMessage: (data: string) => void
    onError?: (error: any) => void
    onDone?: () => void
    onEvent?: (eventType: string, data: string) => void
  }
) {
  const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token') || ''

  return fetchSSE('/api/v1/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(params),
    onMessage: callbacks.onMessage,
    onError: callbacks.onError,
    onDone: callbacks.onDone,
    onEvent: callbacks.onEvent
  })
}
