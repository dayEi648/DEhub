/**
 * 私信消息视图对象
 */
export interface PrivateMessageVO {
  id: number
  senderId?: number
  senderName?: string
  senderAvatar?: string
  receiverId?: number
  conversationKey?: string
  content?: string
  isRead?: boolean
  createTime?: string
}

/**
 * 会话列表视图对象
 */
export interface ConversationVO {
  conversationKey?: string
  otherUserId?: number
  otherUserName?: string
  otherUserAvatar?: string
  lastMessage?: string
  lastMessageTime?: string
  unreadCount?: number
}

/**
 * 发送私信传输对象
 */
export interface PrivateMessageDTO {
  receiverId: number
  content: string
}

/**
 * 分页数据包装
 */
export interface PageDataVo<T> {
  total: number
  records: T[]
}
