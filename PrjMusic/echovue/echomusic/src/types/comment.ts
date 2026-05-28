/**
 * 评论视图对象
 * 对应后端 CommentVO
 */
export interface CommentVO {
  id: number
  inMusic?: boolean
  inPlaylist?: boolean
  inSpace?: boolean
  musicId?: number
  playlistId?: number
  spaceId?: number
  sceneType?: string
  sceneId?: number
  userId?: number
  userName?: string
  content?: string
  likeIds?: number[]
  dislikeIds?: number[]
  likeCount?: number
  dislikeCount?: number
  answerCount?: number
  isReply?: boolean
  replyUserId?: number
  replyCommentId?: number
  isNestedReply?: boolean
  nestedReplyUserId?: number
  nestedReplyCommentId?: number
  safety?: number
  isRecommended?: boolean
  isDeleted?: boolean
  createTime?: string
  updateTime?: string
}

/**
 * 评论数据传输对象（新增/修改/回复）
 * 对应后端 CommentDTO
 */
export interface CommentDTO {
  id?: number
  sceneType: string
  sceneId: number
  content: string
  userId: number
  userName: string
  isReply?: boolean
  replyUserId?: number
  replyCommentId?: number
  isNestedReply?: boolean
  nestedReplyUserId?: number
  nestedReplyCommentId?: number
}

/**
 * 评论分页查询参数
 * 对应后端 CommentPageDTO
 */
export interface CommentPageQuery {
  pageNum: number
  pageSize: number
  sceneType?: string
  sceneId?: number
  userId?: number
  replyCommentId?: number
  nestedReplyCommentId?: number
  isReply?: boolean
  isRecommended?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}
