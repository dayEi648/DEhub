export type AIMessageRole = 'user' | 'assistant' | 'system' | 'tool'

export interface AIConversationItem {
  id: number
  title: string
  created_at: string
  updated_at: string
  last_message_at: string | null
}

export interface AIConversationListResponse {
  items: AIConversationItem[]
  total: number
}

export interface AIConversationListParams {
  skip?: number
  limit?: number
}

export interface AIMessage {
  id: number
  conversation_id: number
  role: AIMessageRole
  content: string
  meta: Record<string, unknown> | null
  created_at: string
}

export interface AIMessageListParams {
  skip?: number
  limit?: number
  include_hidden?: boolean
}

export interface AIChatRequest {
  conversation_id?: number
  user_input: string
  skip_side_effects?: boolean
  is_edit?: boolean
}

export interface AIChatResponse {
  response: string
  conversation_id: number
}
