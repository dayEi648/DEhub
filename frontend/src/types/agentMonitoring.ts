export interface AgentTrace {
  id: number
  trace_id: string
  conversation_id: number | null
  user_id: number | null
  graph_name: string
  status: string
  input_message: string | null
  output_message: string | null
  total_tokens: number | null
  prompt_tokens: number | null
  completion_tokens: number | null
  tool_calls_count: number
  node_steps: number
  latency_ms: number | null
  started_at: string
  ended_at: string | null
  error_type: string | null
  error_message: string | null
  is_flagged: boolean
  meta: Record<string, unknown> | null
}

export interface AgentSpan {
  id: number
  trace_id: string
  parent_span_id: number | null
  span_type: string
  span_name: string
  status: string
  started_at: string
  ended_at: string | null
  latency_ms: number | null
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  error_info: Record<string, unknown> | null
  token_usage: Record<string, unknown> | null
  meta: Record<string, unknown> | null
}

export interface AgentEvaluation {
  id: number
  trace_id: string
  conversation_id: number | null
  eval_type: string
  dimension: string
  score: number
  reason: string | null
  evaluated_at: string
  evaluator_model: string | null
  meta: Record<string, unknown> | null
}

export interface AgentTraceListResponse {
  items: AgentTrace[]
  total: number
}

export interface AgentSpanListResponse {
  items: AgentSpan[]
}

export interface AgentTraceStatsResponse {
  total: number
  today_count: number
  failed_count: number
  avg_latency_ms: number
}

export interface AgentTraceListParams {
  skip?: number
  limit?: number
  conversation_id?: number
  user_id?: number
  status?: string
  is_flagged?: boolean
}

export interface AgentEvaluationListResponse {
  items: AgentEvaluation[]
  total: number
}

export interface AgentEvaluationStatsResponse {
  total_evaluations: number
  avg_score: number
  low_score_count: number
  dimension_avgs: Array<{
    dimension: string
    avg_score: number
  }>
}

export interface AgentEvaluationTrendResponse {
  items: Array<{
    date: string
    count: number
    avg_score: number
  }>
}

export interface AgentEvaluationListParams {
  skip?: number
  limit?: number
  dimension?: string
  min_score?: number
  max_score?: number
}
