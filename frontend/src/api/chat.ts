import client from './client'
import type { ConversationListResponse, MessageResponse } from '@/types'

export function fetchConversations(params?: { skip?: number; limit?: number }) {
  return client.get<ConversationListResponse>('/chat/conversations', { params })
}

export function fetchMessages(conversationId: number, params?: { skip?: number; limit?: number }) {
  return client.get<MessageResponse[]>(`/chat/conversations/${conversationId}/messages`, { params })
}

export function deleteConversation(id: number) {
  return client.delete(`/chat/conversations/${id}`)
}
