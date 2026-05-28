/** 登录/注册接口返回：用户资料 + JWT */
export interface AuthResponse {
  user: UserVO
  token: string
}

/**
 * 用户视图对象
 */
export interface UserVO {
  id: number
  username: string
  name?: string
  role?: number
  gender?: number
  status?: number
  exp?: number
  level?: number
  nextLevelExp?: number
  levelProgress?: number
  safety?: number
  likeCount?: number
  fanCount?: number
  followCount?: number
  songCount?: number
  collectPlaylistIds?: number[]
  collectAlbumIds?: number[]
  collectPlaylistCount?: number
  collectAlbumCount?: number
  collectMusicIds?: number[]
  collectMusicCount?: number
  professional?: boolean
  emoTags?: string[]
  interestTags?: string[]
  fanIds?: number[]
  followIds?: number[]
  songIds?: number[]
  avatar?: string
  city?: string
  description?: string
  birth?: string
  loginTime?: string
  updateTime?: string
  createTime?: string
  isDeleted?: boolean
}

/**
 * 用户传输对象（新增/编辑）
 * 管理端保存接口为 multipart，请求体请使用 `@/api/user` 的 `UserSavePayload` 与 `addUser` / `updateUser`。
 */
export interface UserDTO {
  id?: number
  username: string
  password?: string
  name?: string
  role?: number
  gender?: number
  status?: number
  exp?: number
  avatar?: string
  city?: string
  description?: string
  birth?: string
  emoTags?: string[]
  interestTags?: string[]
  professional?: boolean
}

/**
 * 用户分页查询参数
 */
export interface UserPageQuery {
  pageNum: number
  pageSize: number
  username?: string
  name?: string
  role?: number
  status?: number
  professional?: boolean
  includeDeleted?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * 分页数据包装
 */
export interface PageDataVo<T> {
  total: number
  records: T[]
}

/**
 * 统一响应结构
 */
export interface Result<T> {
  code: number
  msg: string
  data: T
}

/**
 * 性别枚举
 */
export enum Gender {
  UNKNOWN = 0,
  MALE = 1,
  FEMALE = 2
}

/**
 * 状态枚举
 * 0=正常，1=禁言，2=限制，3=封号
 */
export enum UserStatus {
  NORMAL = 0,
  MUTED = 1,
  LIMITED = 2,
  BANNED = 3
}

/**
 * 角色/权限枚举
 * 0=普通用户，1=VIP用户，2=管理员，3=超级管理员
 */
export enum UserRole {
  USER = 0,
  VIP = 1,
  ADMIN = 2,
  SUPER_ADMIN = 3
}

/**
 * 性别选项
 */
export const genderOptions = [
  { label: '未知', value: Gender.UNKNOWN },
  { label: '男', value: Gender.MALE },
  { label: '女', value: Gender.FEMALE }
]

/**
 * 状态选项
 * 0=正常，1=禁言，2=限制，3=封号
 */
export const statusOptions = [
  { label: '正常', value: UserStatus.NORMAL, type: 'success' as const },
  { label: '禁言', value: UserStatus.MUTED, type: 'warning' as const },
  { label: '限制', value: UserStatus.LIMITED, type: 'danger' as const },
  { label: '封号', value: UserStatus.BANNED, type: 'danger' as const }
]

/**
 * 权限选项
 * 0=普通用户，1=VIP用户，2=管理员，3=超级管理员
 */
export const roleOptions = [
  { label: '普通用户', value: UserRole.USER },
  { label: 'VIP用户', value: UserRole.VIP },
  { label: '管理员', value: UserRole.ADMIN },
  { label: '超级管理员', value: UserRole.SUPER_ADMIN }
]

/**
 * 排序字段选项
 */
export const sortFieldOptions = [
  { label: '经验值', value: 'exp' },
  { label: '状态', value: 'status' },
  { label: '创建时间', value: 'create_time' },
  { label: '最后登录', value: 'login_time' },
  { label: '安全等级', value: 'safety' },
  { label: '点赞数', value: 'like_count' }
]

/**
 * 排序方向选项
 */
export const sortOrderOptions = [
  { label: '升序', value: 'asc' },
  { label: '降序', value: 'desc' }
]
