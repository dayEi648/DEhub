import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { ForumZoneResponse } from '@/types'
import * as followApi from '@/api/follow'
import { useUiStore } from './ui'

export const useFollowStore = defineStore('follow', () => {
  const uiStore = useUiStore()

  /* ---------- state ---------- */
  const followedZones = ref<ForumZoneResponse[]>([])
  const followedZoneIds = ref<number[]>([])
  const totalFollowedZones = ref(0)

  /* ---------- zone follows ---------- */

  async function fetchFollowedZones(query?: { skip?: number; limit?: number }) {
    const { data } = await followApi.fetchFollowedZones(query)
    followedZones.value = data.items
    totalFollowedZones.value = data.total
    followedZoneIds.value = data.items.map((item) => item.id)
    return data
  }

  async function followZone(zoneId: number) {
    const { data } = await followApi.followZone(zoneId)
    if (!followedZoneIds.value.includes(zoneId)) {
      followedZoneIds.value.push(zoneId)
    }
    uiStore.showToast('关注成功', 'success')
    return data
  }

  async function unfollowZone(zoneId: number) {
    const { data } = await followApi.unfollowZone(zoneId)
    followedZoneIds.value = followedZoneIds.value.filter((id) => id !== zoneId)
    followedZones.value = followedZones.value.filter((item) => item.id !== zoneId)
    totalFollowedZones.value = Math.max(0, totalFollowedZones.value - 1)
    uiStore.showToast('已取消关注', 'success')
    return data
  }

  return {
    followedZones,
    followedZoneIds,
    totalFollowedZones,
    fetchFollowedZones,
    followZone,
    unfollowZone
  }
})
