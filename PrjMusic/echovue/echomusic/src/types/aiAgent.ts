/**
 * AI 会话
 */
export interface AiSession {
  session_id: string
  title?: string
  update_time?: string
  create_time?: string
}

/**
 * AI 消息
 */
export interface AiMessage {
  id?: number
  role: 'user' | 'assistant'
  content: string
  create_time?: string
}

/**
 * 对话请求
 */
export interface ChatRequest {
  message: string
  session_id?: string
}

/**
 * 非流式对话响应
 */
export interface ChatResponse {
  reply: string
  session_id: string
  intent: string
  tool_results: ToolResult[]
}

/**
 * 音乐项（工具返回）
 */
export interface MusicItem {
  id: number
  name: string
  cover_url?: string
  file_url?: string
  vip?: boolean
  hot?: number
  author_ids?: number[]
}

/**
 * 工具调用结果
 */
export interface ToolResult {
  tool: string
  status: string
  message?: string
  recommendations?: MusicItem[]
  results?: MusicItem[]
  data?: MusicItem
  keyword?: string
  query?: string
  playlists?: any[]
  [key: string]: any
}

/**
 * SSE 流式回调
 */
export interface SseCallbacks {
  onToolEnd?: (data: ToolResult) => void
  onMessageDelta?: (content: string) => void
  onDone?: (data: { session_id: string; intent: string }) => void
  onError?: (msg: string) => void
}
