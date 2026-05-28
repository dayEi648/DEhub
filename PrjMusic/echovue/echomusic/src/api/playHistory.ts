import { get, post } from '@/utils/request'
import type { PlayHistoryVO, PageDataVo } from '@/types/playHistory'

/**
 * 查询当前用户的播放历史
 */
export function getPlayHistoryByUser(userId: number): Promise<PlayHistoryVO[]> {
  return get('/play-history', { userId })
}

/**
 * 分页查询当前用户的播放历史
 */
export function getPlayHistoryPage(userId: number, pageNum: number, pageSize: number): Promise<PageDataVo<PlayHistoryVO>> {
  return get('/play-history/page', { userId, pageNum, pageSize })
}

/**
 * 记录播放历史
 */
export function recordPlayHistory(data: { userId: number; songId: number }): Promise<void> {
  return post('/play-history', data)
}
