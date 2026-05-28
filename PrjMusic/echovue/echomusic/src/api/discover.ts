import { get } from '@/utils/request'
import type { MusicPageQuery, MusicVO, PageDataVo } from '@/types/music'
import type { PlaylistPageQuery, PlaylistVO } from '@/types/playlist'
import type { AlbumPageQuery, AlbumVO } from '@/types/album'

// Re-export existing APIs for convenience
export { getMusicPage, getHomeHotMusics, getHomeNewMusics } from '@/api/music'
export { getPlaylistPage, getHomeRecommendPlaylists } from '@/api/playlist'
export { getAlbumPage } from '@/api/album'

/**
 * 获取高频标签列表
 * @param type 标签类型：emotion / interest / style / instrument / language
 * @param limit 返回数量上限
 */
export function getTopTags(type: string, limit?: number): Promise<string[]> {
  return get('/musics/top-tags', { type, limit })
}

/**
 * 首页推荐专辑
 */
export function getHomeRecommendAlbums(): Promise<AlbumVO[]> {
  return get('/albums/home-recommend')
}

/**
 * 新歌榜查询参数构建（自动设置 createTimeAfter 为1个月前）
 */
export function buildNewSongsQuery(
  pageNum: number,
  pageSize: number,
  sortBy?: string,
  sortOrder?: 'asc' | 'desc'
): MusicPageQuery {
  const oneMonthAgo = new Date()
  oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1)
  const createTimeAfter = oneMonthAgo.toISOString().slice(0, 10) + 'T00:00:00'

  return {
    pageNum,
    pageSize,
    createTimeAfter,
    sortBy: sortBy || 'hot',
    sortOrder: sortOrder || 'desc'
  }
}
