/**
 * 空间说说视图对象
 */
export interface SpacePostVO {
  id: number
  userId?: number
  userName?: string
  userAvatar?: string
  content?: string
  images?: string[]
  postType?: string
  sourceId?: number
  sourceUserName?: string
  sourceUserAvatar?: string
  sourceContent?: string
  sourceImages?: string[]
  extra?: string
  isPrivate?: boolean
  likeIds?: number[]
  likeCount?: number
  commentCount?: number
  forwardCount?: number
  liked?: boolean
  createTime?: string
  updateTime?: string
}

/**
 * 空间说说新增数据传输对象
 */
export interface SpacePostDTO {
  content: string
  images?: string[]
  isPrivate?: boolean
  extra?: string
}

/**
 * 空间说说转发数据传输对象
 */
export interface SpacePostForwardDTO {
  sourceId: number
  content?: string
}

/**
 * 空间说说分页查询参数
 */
export interface SpacePostPageQuery {
  pageNum: number
  pageSize: number
  userId?: number
}
