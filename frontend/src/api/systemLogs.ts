import request from '../utils/request'
import type { SystemLog, SystemLogListResponse, SystemLogStatsResponse, LogListParams } from '../types/systemLog'

export function getLogList(params: LogListParams = {}) {
  return request.get<SystemLogListResponse>('/system_logs/', { params })
}

export function getLogStats() {
  return request.get<SystemLogStatsResponse>('/system_logs/stats')
}

export function batchResolveLogs(ids: number[]) {
  return request.post<{ resolved_count: number }>('/system_logs/batch_resolve', { ids })
}

export function resolveLog(logId: number) {
  return request.post<SystemLog>(`/system_logs/${logId}/resolve`)
}

export function deleteLog(logId: number) {
  return request.delete(`/system_logs/${logId}`)
}
