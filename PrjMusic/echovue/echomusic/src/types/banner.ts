export type BannerTargetType = 'MUSIC' | 'ALBUM'

export interface BannerVO {
  id: string
  title: string
  description: string
  targetType: BannerTargetType
  targetId: number
  coverUrl: string
  targetName: string
  sortOrder: number
}

export interface BannerSavePayload {
  title: string
  description: string
  targetType: BannerTargetType
  targetId: number
}
