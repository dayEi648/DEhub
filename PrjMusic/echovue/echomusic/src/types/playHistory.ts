/**
 * 播放历史视图对象
 * 对应后端 PlayHistoryVO
 */
export interface PlayHistoryVO {
  id: number
  userId?: number
  songId?: number
  playedAt?: string
  musicName?: string
  coverUrl?: string
  fileUrl?: string
  authorNames?: string[]
  albumId?: number
  albumName?: string
}

/**
 * 分页数据包装对象
 */
export interface PageDataVo<T> {
  total: number
  records: T[]
}
