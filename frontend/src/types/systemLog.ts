export type LogLevel = 'WARN' | 'ERROR' | 'CRITICAL'

export interface SystemLog {
  id: number
  level: LogLevel
  module: string | null
  message: string
  exception: string | null
  trace_id: string | null
  user_id: number | null
  ip: string | null
  extra: Record<string, unknown> | null
  is_resolved: boolean
  resolved_at: string | null
  resolved_by: number | null
  created_at: string
}

export interface SystemLogListResponse {
  items: SystemLog[]
  total: number
}

export interface SystemLogStatsResponse {
  total: number
  total_unresolved: number
  warn_count: number
  error_count: number
  critical_count: number
}

export interface LogListParams {
  skip?: number
  limit?: number
  level?: LogLevel
  is_resolved?: boolean
  module?: string
  created_after?: string
  created_before?: string
}
