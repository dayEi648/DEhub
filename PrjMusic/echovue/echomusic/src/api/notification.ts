import { get, put } from '@/utils/request'
import type {
  NotificationVO,
  NotificationPageQuery,
  NotificationUnreadCount,
  PageDataVo
} from '@/types/notification'

/**
 * 获取未读通知统计（含私信）
 */
export function getUnreadCount(): Promise<NotificationUnreadCount> {
  return get('/notifications/unread-count')
}

/**
 * 分页查询通知列表
 */
export function getNotifications(params: NotificationPageQuery): Promise<PageDataVo<NotificationVO>> {
  return get('/notifications', params)
}

/**
 * 批量标记通知为已读
 */
export function readNotifications(ids: number[]): Promise<void> {
  return put('/notifications/read', ids)
}

/**
 * 按分类全部标记为已读
 * @param category 通知分类，空字符串表示全部
 */
export function readAllNotifications(category?: string): Promise<void> {
  return put('/notifications/read-all', undefined, { params: category ? { category } : {} })
}
