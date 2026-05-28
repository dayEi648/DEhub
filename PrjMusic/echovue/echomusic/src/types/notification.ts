/**
 * 通知视图对象
 */
export interface NotificationVO {
  id: number
  userId?: number
  type?: string
  senderId?: number
  senderName?: string
  senderAvatar?: string
  sourceType?: string
  sourceId?: number
  sourceParentId?: number
  title?: string
  content?: string
  extra?: string
  isRead?: boolean
  readTime?: string
  createTime?: string
}

/**
 * 通知未读数统计
 */
export interface NotificationUnreadCount {
  total: number
  mention: number
  reply: number
  notify: number
  privateMessage: number
}

/**
 * 通知分页查询参数
 */
export interface NotificationPageQuery {
  pageNum: number
  pageSize: number
  type?: string
  category?: string
  unreadOnly?: boolean
}

/**
 * 分页数据包装
 */
export interface PageDataVo<T> {
  total: number
  records: T[]
}

/**
 * 通知类型选项
 */
export const notificationTypeMap: Record<string, string> = {
  mention: '@我的',
  reply: '回复',
  comment: '评论',
  follow: '关注',
  collect: '收藏',
  like: '点赞',
  system: '系统'
}
