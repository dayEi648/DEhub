/**
 * 歌单视图对象
 * 对应后端 PlaylistVO
 */
export interface PlaylistVO {
  id: number
  playlistName: string
  userId?: number
  userName?: string
  isPrivate?: boolean
  listDescription?: string
  songIds?: number[]
  emoTags?: string[]
  interestTags?: string[]
  collectCount?: number
  playCount?: number
  isLike?: boolean
  hot?: number
  commentCount?: number
  isRecommended?: boolean
  imageUrl?: string
  createTime?: string
  updateTime?: string
}

/**
 * 歌单分页查询参数
 * 对应后端 PlaylistPageDTO
 */
export interface PlaylistPageQuery {
  pageNum: number
  pageSize: number
  playlistName?: string
  userId?: number
  userName?: string
  songIds?: number[]
  emoTags?: string[]
  interestTags?: string[]
  isPrivate?: boolean
  isLike?: boolean
  isRecommended?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * 分页数据包装对象
 */
export interface PageDataVo<T> {
  total: number
  records: T[]
}

// 排序字段选项
export const sortFieldOptions = [
  { label: '创建时间', value: 'create_time' },
  { label: '更新时间', value: 'update_time' },
  { label: '热度', value: 'hot' },
  { label: '播放数', value: 'play_count' },
  { label: '评论数', value: 'comment_count' },
  { label: '收藏数', value: 'collect_count' }
]

// 排序方向选项
export const sortOrderOptions = [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' }
]
