/**
 * 专辑视图对象
 * 对应后端 AlbumVO
 */
export interface AlbumVO {
  id: number
  albumName: string
  authorIds?: number[]
  authorNames?: string[]
  authorNameList?: string[]
  albumDescription?: string
  source?: string
  emoTags?: string[]
  interestTags?: string[]
  collectCount?: number
  playCount?: number
  hot?: number
  image1Url?: string
  image2Url?: string
  songIds?: number[]
  songNameList?: string[]
  isRecommended?: boolean
  isDeleted?: boolean
  createTime?: string
  updateTime?: string
}

/**
 * 专辑数据传输对象（新增/编辑）
 * 对应后端 AlbumDTO；文件请通过 `@/api/album` 中 `AlbumSavePayload` + `addAlbum` / `updateAlbum`（multipart）上传
 */
export interface AlbumDTO {
  id?: number
  albumName: string
  authorIds?: number[]
  authorNames?: string[]
  albumDescription?: string
  source?: string
  emoTags?: string[]
  interestTags?: string[]
  image1Url?: string
  image2Url?: string
  songIds?: number[]
  isRecommended?: boolean
}

/**
 * 专辑分页查询参数
 * 对应后端 AlbumPageDTO
 */
export interface AlbumPageQuery {
  pageNum: number
  pageSize: number
  albumName?: string
  authorName?: string
  authorIds?: number[]
  songIds?: number[]
  emoTags?: string[]
  interestTags?: string[]
  isRecommended?: boolean
  isDeleted?: boolean
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
  { label: '收藏数', value: 'collect_count' }
]

// 排序方向选项
export const sortOrderOptions = [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' }
]
