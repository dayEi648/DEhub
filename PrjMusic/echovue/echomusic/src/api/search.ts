import { get } from '@/utils/request'
import type { MusicVO, PageDataVo } from '@/types/music'
import type { PlaylistVO } from '@/types/playlist'
import type { AlbumVO } from '@/types/album'
import type { UserVO } from '@/types/user'

export interface SearchResultVO {
  musics: MusicVO[]
  playlists: PlaylistVO[]
  albums: AlbumVO[]
  singers: UserVO[]
}

export function searchAll(keyword: string): Promise<SearchResultVO> {
  return get('/search/all', { keyword })
}

export function searchMusics(keyword: string, pageNum: number, pageSize: number): Promise<PageDataVo<MusicVO>> {
  return get('/search/musics', { keyword, pageNum, pageSize })
}

export function searchPlaylists(keyword: string, pageNum: number, pageSize: number): Promise<PageDataVo<PlaylistVO>> {
  return get('/search/playlists', { keyword, pageNum, pageSize })
}

export function searchAlbums(keyword: string, pageNum: number, pageSize: number): Promise<PageDataVo<AlbumVO>> {
  return get('/search/albums', { keyword, pageNum, pageSize })
}

export function searchSingers(keyword: string, pageNum: number, pageSize: number): Promise<PageDataVo<UserVO>> {
  return get('/search/singers', { keyword, pageNum, pageSize })
}

export function searchUsers(keyword: string, pageNum: number, pageSize: number): Promise<PageDataVo<UserVO>> {
  return get('/search/users', { keyword, pageNum, pageSize })
}
