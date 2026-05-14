import client from './client'
import type {
  FollowStatusResponse,
  ZoneFollowListResponse
} from '@/types'

/* ---------- Zone Follows ---------- */

export function followZone(zoneId: number) {
  return client.post<FollowStatusResponse>(`/follows/zones/${zoneId}`)
}

export function unfollowZone(zoneId: number) {
  return client.delete<FollowStatusResponse>(`/follows/zones/${zoneId}`)
}

export function fetchFollowedZones(params?: { skip?: number; limit?: number }) {
  return client.get<ZoneFollowListResponse>('/follows/zones', { params })
}
