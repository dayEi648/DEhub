import { del, get, postForm, putForm } from '@/utils/request'
import { appendStringArrayForMultipart } from '@/utils/formDataAppend'
import type { MusicDTO, MusicPageQuery, MusicVO, PageDataVo } from '@/types/music'

/** 与后端 MusicDTO 中 Multipart 字段名一致 */
export type MusicFilesPayload = {
  file?: File | null
  lyricsFile?: File | null
  image1File?: File | null
  image2File?: File | null
  image3File?: File | null
}

export type MusicSavePayload = MusicDTO & MusicFilesPayload

function buildMusicFormData(data: MusicSavePayload): FormData {
  const fd = new FormData()
  const {
    file,
    lyricsFile,
    image1File,
    image2File,
    image3File,
    fileUrl: _u1,
    lyricsUrl: _u2,
    image1Url: _u3,
    image2Url: _u4,
    image3Url: _u5,
    ...rest
  } = data

  if (rest.id != null) {
    fd.append('id', String(rest.id))
  }
  if (rest.musicName != null) {
    fd.append('musicName', rest.musicName)
  }
  appendStringArrayForMultipart(fd, 'authorIds', rest.authorIds?.map(String))
  if (rest.albumId != null) {
    fd.append('albumId', String(rest.albumId))
  }
  if (rest.vip != null) {
    fd.append('vip', String(rest.vip))
  }
  if (rest.source != null) {
    fd.append('source', rest.source)
  }
  appendStringArrayForMultipart(fd, 'emoTags', rest.emoTags)
  appendStringArrayForMultipart(fd, 'interestTags', rest.interestTags)
  if (rest.style != null) {
    fd.append('style', rest.style)
  }
  appendStringArrayForMultipart(fd, 'languages', rest.languages)
  appendStringArrayForMultipart(fd, 'instruments', rest.instruments)
  if (rest.releaseDate != null && rest.releaseDate !== '') {
    fd.append('releaseDate', rest.releaseDate)
  }
  if (rest.isRecommended != null) {
    fd.append('isRecommended', String(rest.isRecommended))
  }
  if (rest.isDeleted != null) {
    fd.append('isDeleted', String(rest.isDeleted))
  }
  if (rest.hot != null) {
    fd.append('hot', String(rest.hot))
  }

  if (file) {
    fd.append('file', file)
  }
  if (lyricsFile) {
    fd.append('lyricsFile', lyricsFile)
  }
  if (image1File) {
    fd.append('image1File', image1File)
  }
  if (image2File) {
    fd.append('image2File', image2File)
  }
  if (image3File) {
    fd.append('image3File', image3File)
  }

  return fd
}

export function getMusicPage(params: MusicPageQuery): Promise<PageDataVo<MusicVO>> {
  return get('/musics/page', params)
}

export function getMusicById(id: number): Promise<MusicVO> {
  return get(`/musics/${id}`)
}

export function getMusicsByIds(ids: number[]): Promise<MusicVO[]> {
  if (ids.length === 0) return Promise.resolve([])
  return get('/musics/batch', { ids })
}

export function addMusic(data: MusicSavePayload): Promise<void> {
  return postForm('/musics', buildMusicFormData(data))
}

export function updateMusic(data: MusicSavePayload): Promise<void> {
  return putForm('/musics', buildMusicFormData(data))
}

export function deleteMusics(ids: number[]): Promise<void> {
  return del('/musics', { ids })
}

/**
 * 获取音乐歌词文本
 */
export function getMusicLyrics(id: number): Promise<string> {
  return get(`/musics/${id}/lyrics`)
}

/**
 * 首页热门音乐
 */
export function getHomeHotMusics(): Promise<MusicVO[]> {
  return get('/musics/home-hot')
}

/**
 * 首页新歌速递
 */
export function getHomeNewMusics(): Promise<MusicVO[]> {
  return get('/musics/home-new')
}

/**
 * 推荐与指定音乐标签相似的其他音乐
 */
export function getRecommendMusics(id: number): Promise<MusicVO[]> {
  return get(`/musics/recommend/${id}`)
}
