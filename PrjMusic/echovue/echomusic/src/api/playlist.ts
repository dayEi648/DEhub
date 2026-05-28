import { get, post, put, del, postForm } from '@/utils/request'
import type { PlaylistVO, PlaylistPageQuery, PageDataVo } from '@/types/playlist'

/**
 * 分页查询歌单
 */
export function getPlaylistPage(params: PlaylistPageQuery): Promise<PageDataVo<PlaylistVO>> {
  return get('/playlists/page', params)
}

/**
 * 首页推荐歌单
 */
export function getHomeRecommendPlaylists(): Promise<PlaylistVO[]> {
  return get('/playlists/home-recommend')
}

/**
 * 根据ID查询歌单详情
 */
export function getPlaylistById(id: number): Promise<PlaylistVO> {
  return get(`/playlists/${id}`)
}

/**
 * 上传歌单封面
 */
export function uploadPlaylistCover(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  return postForm('/playlists/cover', formData)
}

/** 添加歌曲到歌单 */
export function addSongToPlaylist(playlistId: number, musicId: number): Promise<number[]> {
  return post(`/playlists/${playlistId}/songs/${musicId}`)
}

/** 从歌单移除歌曲 */
export function removeSongFromPlaylist(playlistId: number, musicId: number): Promise<number[]> {
  return del(`/playlists/${playlistId}/songs/${musicId}`)
}

/**
 * 新增歌单
 */
export function addPlaylist(data: Partial<PlaylistVO>): Promise<void> {
  return post('/playlists', data)
}

/**
 * 修改歌单
 */
export function updatePlaylist(data: Partial<PlaylistVO> & { id: number }): Promise<void> {
  return put('/playlists', data)
}

/**
 * 根据ID删除歌单
 */
export function deletePlaylist(id: number): Promise<void> {
  return del(`/playlists/${id}`)
}

/**
 * 批量删除歌单
 */
export function deletePlaylists(ids: number[]): Promise<void> {
  return del('/playlists', { ids })
}

/**
 * 推荐包含指定音乐的歌单
 */
export function getRecommendPlaylists(musicId: number): Promise<PlaylistVO[]> {
  return get(`/playlists/recommend/${musicId}`)
}
