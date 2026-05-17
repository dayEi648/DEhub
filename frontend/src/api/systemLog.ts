import client from './client'
import type {
  SystemLogListResponse,
  SystemLogResponse,
  SystemLogStatsResponse,
} from '@/types'

export function fetchSystemLogs(params?: {
  skip?: number
  limit?: number
  level?: string
  is_resolved?: boolean
  module?: string
  created_after?: string
  created_before?: string
}) {
  return client.get<SystemLogListResponse>('/system_logs/', { params })
}

export function fetchSystemLogStats() {
  return client.get<SystemLogStatsResponse>('/system_logs/stats')
}

export function fetchSystemLogById(id: number) {
  return client.get<SystemLogResponse>(`/system_logs/${id}`)
}

export function resolveSystemLog(id: number) {
  return client.post<SystemLogResponse>(`/system_logs/${id}/resolve`)
}

export function batchResolveSystemLogs(ids: number[]) {
  return client.post<{ resolved_count: number }>('/system_logs/batch_resolve', {
    ids,
  })
}

export function deleteSystemLog(id: number) {
  return client.delete(`/system_logs/${id}`)
}
