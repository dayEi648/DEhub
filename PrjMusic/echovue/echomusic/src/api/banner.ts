import { get, post, put, del } from '@/utils/request'
import type { BannerVO, BannerSavePayload } from '@/types/banner'

export function getBanners(): Promise<BannerVO[]> {
  return get('/banners')
}

export function addBanner(data: BannerSavePayload): Promise<void> {
  return post('/banners', data)
}

export function updateBanner(id: string, data: BannerSavePayload): Promise<void> {
  return put(`/banners/${id}`, data)
}

export function deleteBanner(id: string): Promise<void> {
  return del(`/banners/${id}`)
}

export function reorderBanner(ids: string[]): Promise<void> {
  return put('/banners/order', ids)
}
