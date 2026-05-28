import { get, post, put, del, postForm, putForm } from '@/utils/request'
import { appendStringArrayForMultipart } from '@/utils/formDataAppend'
import type {
  UserVO,
  UserDTO,
  UserPageQuery,
  PageDataVo,
  AuthResponse
} from '@/types/user'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'

/**
 * 管理端新增/编辑：multipart，头像字段名为 avatarFile（与后端 UserDTO 一致）
 */
export type UserSavePayload = UserDTO & {
  avatarFile?: File | null
}

function buildUserFormData(data: UserSavePayload, mode: 'add' | 'update'): FormData {
  const fd = new FormData()

  if (mode === 'update' && data.id != null) {
    fd.append('id', String(data.id))
  }

  if (data.username != null) {
    fd.append('username', data.username)
  }

  if (mode === 'add') {
    if (data.password != null) {
      fd.append('password', data.password)
    }
  } else if (data.password != null && data.password !== '') {
    fd.append('password', data.password)
  }

  if (data.name != null) {
    fd.append('name', data.name)
  }
  if (data.role != null) {
    fd.append('role', String(data.role))
  }
  if (data.gender != null) {
    fd.append('gender', String(data.gender))
  }
  if (data.status != null) {
    fd.append('status', String(data.status))
  }
  if (data.exp != null) {
    fd.append('exp', String(data.exp))
  }
  if (data.city != null && data.city !== '') {
    fd.append('city', data.city)
  }
  if (data.description != null && data.description !== '') {
    fd.append('description', data.description)
  }
  if (data.birth != null && data.birth !== '') {
    fd.append('birth', data.birth)
  }
  if (data.professional != null) {
    fd.append('professional', String(data.professional))
  }

  appendStringArrayForMultipart(fd, 'emoTags', data.emoTags)
  appendStringArrayForMultipart(fd, 'interestTags', data.interestTags)

  if (data.avatarFile) {
    fd.append('avatarFile', data.avatarFile)
  }

  return fd
}

/**
 * 分页查询用户
 * @param params 查询参数
 */
export function getUserPage(params: UserPageQuery): Promise<PageDataVo<UserVO>> {
  return get('/users/page', params)
}

/**
 * 根据ID查询用户
 * @param id 用户ID
 */
export function getUserById(id: number): Promise<UserVO> {
  return get(`/users/${id}`)
}

/**
 * 新增用户
 */
export function addUser(data: UserSavePayload): Promise<void> {
  return postForm('/users', buildUserFormData(data, 'add'))
}

/**
 * 编辑用户
 */
export function updateUser(data: UserSavePayload): Promise<void> {
  return putForm('/users', buildUserFormData(data, 'update'))
}

/**
 * 注销用户（逻辑删除）
 * @param id 用户ID
 */
export function cancelUser(id: number): Promise<void> {
  return put(`/users/${id}/delete`)
}

/**
 * 删除用户（物理删除）
 * @param ids 用户ID数组
 */
export function deleteUsers(ids: number[]): Promise<void> {
  return del('/users', { ids })
}

/**
 * 登录
 */
export function login(data: Pick<UserDTO, 'username' | 'password'>): Promise<AuthResponse> {
  return post('/users/login', data)
}

/**
 * 注册（成功后返回与登录相同的 AuthResponse）
 */
export function register(data: Pick<UserDTO, 'username' | 'password' | 'name'>): Promise<AuthResponse> {
  return post('/users/register', data)
}

/**
 * 退出登录（服务端更新 login_time 后前端再清 token）
 */
export function logout(): Promise<void> {
  return post('/users/logout')
}

/**
 * 当前登录用户更新个人资料（multipart，支持头像上传）
 */
export function updateProfile(data: {
  name?: string
  gender?: number
  city?: string
  description?: string
  birth?: string
  avatarFile?: File | null
}): Promise<UserVO> {
  const fd = new FormData()
  if (data.name != null) fd.append('name', data.name)
  if (data.gender != null) fd.append('gender', String(data.gender))
  if (data.city != null && data.city !== '') fd.append('city', data.city)
  if (data.description != null && data.description !== '') fd.append('description', data.description)
  if (data.birth != null && data.birth !== '') fd.append('birth', data.birth)
  if (data.avatarFile) fd.append('avatarFile', data.avatarFile)
  return putForm('/users/profile', fd)
}

/** 查询当前用户收藏的歌单列表 */
export function getCollectedPlaylists(): Promise<PlaylistVO[]> {
  return get('/users/collections/playlists')
}

/** 分页查询当前用户收藏的歌单列表 */
export function getCollectedPlaylistsPage(pageNum: number, pageSize: number): Promise<PageDataVo<PlaylistVO>> {
  return get('/users/collections/playlists/page', { pageNum, pageSize })
}

/** 查询当前用户收藏的专辑列表 */
export function getCollectedAlbums(): Promise<AlbumVO[]> {
  return get('/users/collections/albums')
}

/** 分页查询当前用户收藏的专辑列表 */
export function getCollectedAlbumsPage(pageNum: number, pageSize: number): Promise<PageDataVo<AlbumVO>> {
  return get('/users/collections/albums/page', { pageNum, pageSize })
}

/** 收藏歌单 */
export function collectPlaylist(id: number): Promise<void> {
  return post(`/users/collections/playlists/${id}`)
}

/** 取消收藏歌单 */
export function uncollectPlaylist(id: number): Promise<void> {
  return del(`/users/collections/playlists/${id}`)
}

/** 收藏专辑 */
export function collectAlbum(id: number): Promise<void> {
  return post(`/users/collections/albums/${id}`)
}

/** 取消收藏专辑 */
export function uncollectAlbum(id: number): Promise<void> {
  return del(`/users/collections/albums/${id}`)
}

/** 关注用户 */
export function followUser(id: number): Promise<void> {
  return post(`/users/${id}/follow`)
}

/** 取消关注用户 */
export function unfollowUser(id: number): Promise<void> {
  return del(`/users/${id}/follow`)
}

/**
 * 根据ID批量查询用户
 * @param ids 用户ID数组
 */
export function getUsersByIds(ids: number[]): Promise<UserVO[]> {
  if (ids.length === 0) return Promise.resolve([])
  return get('/users/batch', { ids })
}

/**
 * 分页查询当前用户的关注列表
 */
export function getFollowsPage(pageNum: number, pageSize: number): Promise<PageDataVo<UserVO>> {
  return get('/users/follows', { pageNum, pageSize })
}

/**
 * 分页查询当前用户的粉丝列表
 */
export function getFansPage(pageNum: number, pageSize: number): Promise<PageDataVo<UserVO>> {
  return get('/users/fans', { pageNum, pageSize })
}
