import request from '../utils/request'
import type {
  ContentModerationRecordListResponse,
  ContentModerationRecord,
  ContentModerationStatsResponse,
  ContentModerationRetryResponse,
  ContentModerationListParams,
} from '../types/contentModeration'

export function getModerationRecords(params: ContentModerationListParams = {}) {
  return request.get<ContentModerationRecordListResponse>('/content_moderation/records', { params })
}

export function getModerationRecord(recordId: number) {
  return request.get<ContentModerationRecord>(`/content_moderation/records/${recordId}`)
}

export function retryModerationRecord(recordId: number) {
  return request.post<ContentModerationRetryResponse>(`/content_moderation/records/${recordId}/retry`)
}

export function getModerationStats() {
  return request.get<ContentModerationStatsResponse>('/content_moderation/stats')
}

export function exportModerationRecords(
  format: 'json' | 'csv' = 'json',
  params: Omit<ContentModerationListParams, 'skip' | 'limit'> = {},
) {
  return request.get('/content_moderation/records/export', {
    params: { format, ...params },
    responseType: 'blob',
  })
}
