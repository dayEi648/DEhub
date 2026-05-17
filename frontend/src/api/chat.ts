import client from './client'
import type { ConversationListResponse, MessageResponse, ChatCreate } from '@/types'

export function fetchConversations(params?: { skip?: number; limit?: number }) {
  return client.get<ConversationListResponse>('/ai_chat/conversations', { params })
}

export function fetchMessages(conversationId: number, params?: { skip?: number; limit?: number }) {
  return client.get<MessageResponse[]>(`/ai_chat/conversations/${conversationId}/messages`, { params })
}

export function deleteConversation(id: number) {
  return client.delete(`/ai_chat/conversations/${id}`)
}

export function sendMessage(params: ChatCreate) {
  return client.post<{ response: string; conversation_id: number }>('/ai_chat/chat', params, {
    skipGlobalLoading: true,
    timeout: 120000,
  } as any)
}
