import { get, postForm, putForm, del } from '@/utils/request'
import type { AlbumVO, AlbumDTO, AlbumPageQuery, PageDataVo } from '@/types/album'
import type { MusicVO } from '@/types/music'

/**
 * 管理端新增/编辑：multipart
 */
export type AlbumSavePayload = AlbumDTO & {
  image1File?: File | null
  image2File?: File | null
}

function buildAlbumFormData(data: AlbumSavePayload, mode: 'add' | 'update'): FormData {
  const fd = new FormData()

  if (mode === 'update' && data.id != null) {
    fd.append('id', String(data.id))
  }

  fd.append('albumName', data.albumName)

  if (data.albumDescription != null && data.albumDescription !== '') {
    fd.append('albumDescription', data.albumDescription)
  }
  if (data.source != null && data.source !== '') {
    fd.append('source', data.source)
  }

  // Integer 数组为 null 时跳过；空数组不 append（与 emoTags 等字符串标签的 multipart 约定不同）
  const appendIdArray = (key: string, arr: number[] | undefined | null) => {
    if (arr == null) return
    if (arr.length > 0) {
      arr.forEach((v) => fd.append(key, String(v)))
    }
  }

  // authorIds / authorNames / emo_tags / interest_tags 由后端按关联歌曲聚合，前端不传标签
  appendIdArray('songIds', data.songIds)

  if (data.isRecommended != null) {
    fd.append('isRecommended', String(data.isRecommended))
  }

  if (data.image1File) {
    fd.append('image1File', data.image1File)
  }
  if (data.image2File) {
    fd.append('image2File', data.image2File)
  }

  return fd
}

/**
 * 分页查询专辑
 */
export function getAlbumPage(params: AlbumPageQuery): Promise<PageDataVo<AlbumVO>> {
  return get('/albums/page', params)
}

/**
 * 根据ID查询专辑详情
 */
export function getAlbumById(id: number): Promise<AlbumVO> {
  return get(`/albums/${id}`)
}

/**
 * 新增专辑
 */
export function addAlbum(data: AlbumSavePayload): Promise<void> {
  return postForm('/albums', buildAlbumFormData(data, 'add'))
}

/**
 * 编辑专辑
 */
export function updateAlbum(data: AlbumSavePayload): Promise<void> {
  return putForm('/albums', buildAlbumFormData(data, 'update'))
}

/**
 * 逻辑删除（下架）专辑
 */
export function cancelAlbum(id: number): Promise<void> {
  return putForm(`/albums/${id}/delete`, new FormData())
}

/**
 * 恢复（上架）专辑
 */
export function restoreAlbum(id: number): Promise<void> {
  return putForm(`/albums/${id}/restore`, new FormData())
}

/**
 * 批量物理删除专辑
 */
export function deleteAlbums(ids: number[]): Promise<void> {
  return del('/albums', { ids })
}

/**
 * 搜索用户（按昵称/用户名模糊匹配）
 */
export function searchUsers(keyword: string, limit = 10): Promise<{ id: number; username: string; name?: string }[]> {
  return get('/users/search', { keyword, limit })
}

/**
 * 搜索音乐（按音乐名模糊匹配）
 */
export function searchMusics(keyword: string, limit = 10): Promise<MusicVO[]> {
  return get('/musics/search', { keyword, limit })
}

/**
 * 搜索专辑（按专辑名模糊匹配）
 */
export function searchAlbums(keyword: string, limit = 10): Promise<{ id: number; albumName: string }[]> {
  return get('/albums/search', { keyword, limit })
}
