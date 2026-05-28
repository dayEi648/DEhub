/**
 * 音乐视图对象
 * 对应后端 MusicVO
 */
export interface MusicVO {
  id: number
  musicName: string
  authorIds?: number[]
  authorNameList?: string[]
  albumId?: number
  albumName?: string
  vip?: boolean
  emoTags?: string[]
  interestTags?: string[]
  source?: string
  fileUrl?: string
  lyricsUrl?: string
  image1Url?: string
  image2Url?: string
  image3Url?: string
  style?: string
  languages?: string[]
  instruments?: string[]
  releaseDate?: string
  collectCount?: number
  commentCount?: number
  playCount?: number
  hot?: number
  hotLevel?: number
  trend?: string
  isRecommended?: boolean
  createTime?: string
  updateTime?: string
  isDeleted?: boolean
}

/**
 * 音乐数据传输对象（新增/编辑）
 * 对应后端 MusicDTO 标量字段；文件请通过 `@/api/music` 的 `MusicSavePayload` 与 `addMusic` / `updateMusic`（multipart）上传。
 */
export interface MusicDTO {
  id?: number
  musicName: string
  authorIds?: string[]
  albumId?: number
  vip?: boolean
  emoTags?: string[]
  interestTags?: string[]
  source?: string
  fileUrl?: string
  lyricsUrl?: string
  image1Url?: string
  image2Url?: string
  image3Url?: string
  style?: string
  languages?: string[]
  instruments?: string[]
  releaseDate?: string
  hot?: number
  isRecommended?: boolean
  isDeleted?: boolean
}

/**
 * 音乐分页查询参数
 * 对应后端 MusicPageDTO
 */
export interface MusicPageQuery {
  pageNum: number
  pageSize: number
  musicName?: string
  style?: string
  vip?: boolean
  albumId?: number
  emoTags?: string[]
  interestTags?: string[]
  isRecommended?: boolean
  isDeleted?: boolean
  authorIds?: number[]
  language?: string[]
  instruments?: string[]
  createTimeAfter?: string
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
  { label: '播放量', value: 'play_count' },
  { label: '评论数', value: 'comment_count' },
  { label: '收藏数', value: 'collect_count' },
  { label: '发行日期', value: 'release_date' }
]

// 排序方向选项
export const sortOrderOptions = [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' }
]

// 角色选项（用于作者关联）
export const roleOptions = [
  { label: '主唱', value: 1 },
  { label: '鼓手', value: 2 },
  { label: '吉他手', value: 3 },
  { label: '贝斯手', value: 4 },
  { label: '键盘手', value: 5 },
  { label: '制作人', value: 6 }
]
