import request from '../utils/request'
import type {
  AIChatRequest,
  AIChatResponse,
  AIConversationListParams,
  AIConversationListResponse,
  AIMessage,
  AIMessageListParams,
} from '../types/aiChat'

export function chatWithAI(data: AIChatRequest) {
  return request.post<AIChatResponse>('/ai_chat/chat', data)
}

export function getConversationList(params: AIConversationListParams = {}) {
  return request.get<AIConversationListResponse>('/ai_chat/conversations', { params })
}

export function getConversationMessages(conversationId: number, params: AIMessageListParams = {}) {
  return request.get<AIMessage[]>(`/ai_chat/conversations/${conversationId}/messages`, { params })
}

export function deleteConversation(conversationId: number) {
  return request.delete(`/ai_chat/conversations/${conversationId}`)
}

