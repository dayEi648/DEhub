import { get, post, put } from '@/utils/request'
import type {
  PrivateMessageVO,
  ConversationVO,
  PrivateMessageDTO,
  PageDataVo
} from '@/types/privateMessage'

/**
 * 获取会话列表
 */
export function getConversations(): Promise<ConversationVO[]> {
  return get('/private-messages/conversations')
}

/**
 * 分页查询某个会话的消息
 */
export function getMessages(
  conversationKey: string,
  pageNum: number = 1,
  pageSize: number = 20
): Promise<PageDataVo<PrivateMessageVO>> {
  return get('/private-messages', { conversationKey, pageNum, pageSize })
}

/**
 * 发送私信
 */
export function sendMessage(data: PrivateMessageDTO): Promise<void> {
  return post('/private-messages', data)
}

/**
 * 标记某会话为已读
 */
export function readMessages(conversationKey: string): Promise<void> {
  return put('/private-messages/read', undefined, { params: { conversationKey } })
}
