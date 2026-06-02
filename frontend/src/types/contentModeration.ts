export type ModerationStatus =
  | 'pending'
  | 'running'
  | 'passed'
  | 'blocked'
  | 'action_failed'
  | 'review_failed'
  | 'stale'

export type ModerationTargetType =
  | 'user'
  | 'blog_post'
  | 'forum_zone'
  | 'forum_post'
  | 'forum_reply'
  | 'comment'

export type RiskLevel = 'none' | 'low' | 'medium' | 'high'

export interface FlaggedSpan {
  field: string
  text: string
  start: number
  end: number
  category: string
  confidence: number
}

export interface ContentModerationRecord {
  id: number
  task_id: string
  trace_id: string | null
  target_type: ModerationTargetType
  target_id: number
  target_version: string
  trigger_action: string
  status: ModerationStatus
  risk_level: RiskLevel
  categories: string[] | null
  original_snapshot: Record<string, unknown>
  moderation_result: Record<string, unknown> | null
  action_plan: Record<string, unknown> | null
  action_result: Record<string, unknown> | null
  model_name: string | null
  error_type: string | null
  error_message: string | null
  created_by_user_id: number | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface ContentModerationRecordListResponse {
  items: ContentModerationRecord[]
  total: number
}

export interface ContentModerationStatsResponse {
  total: number
  today_count: number
  failed_count: number
  blocked_count: number
  avg_latency_ms: number | null
}

export interface ContentModerationRetryResponse {
  id: number
  task_id: string
  status: string
  message: string
}

export interface ContentModerationListParams {
  skip?: number
  limit?: number
  status?: ModerationStatus
  target_type?: ModerationTargetType
  risk_level?: RiskLevel
  user_id?: number
  start_time?: string
  end_time?: string
}
