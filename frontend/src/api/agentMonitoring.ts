import request from '../utils/request'
import type {
  AgentTrace,
  AgentTraceListResponse,
  AgentTraceStatsResponse,
  AgentTraceListParams,
  AgentSpanListResponse,
  AgentEvaluationListResponse,
  AgentEvaluationStatsResponse,
  AgentEvaluationTrendResponse,
  AgentEvaluationListParams,
} from '../types/agentMonitoring'

export function getAgentTraces(params: AgentTraceListParams = {}) {
  return request.get<AgentTraceListResponse>('/agent_monitoring/traces', { params })
}

export function getAgentTrace(traceId: string) {
  return request.get<AgentTrace>(`/agent_monitoring/traces/${traceId}`)
}

export function getAgentTraceSpans(traceId: string) {
  return request.get<AgentSpanListResponse>(`/agent_monitoring/traces/${traceId}/spans`)
}

export function getAgentTraceStats() {
  return request.get<AgentTraceStatsResponse>('/agent_monitoring/stats')
}

// ---------- Phase 3: 质量评估 API ----------

export function getAgentEvaluations(params: AgentEvaluationListParams = {}) {
  return request.get<AgentEvaluationListResponse>('/agent_monitoring/evaluations', { params })
}

export function getAgentEvaluationStats() {
  return request.get<AgentEvaluationStatsResponse>('/agent_monitoring/evaluations/stats')
}

export function getAgentEvaluationTrend(days?: number) {
  return request.get<AgentEvaluationTrendResponse>('/agent_monitoring/evaluations/trend', {
    params: days ? { days } : undefined,
  })
}

export function getTraceEvaluations(traceId: string) {
  return request.get<AgentEvaluationListResponse>(`/agent_monitoring/traces/${traceId}/evaluations`)
}

export function triggerTraceEvaluation(traceId: string) {
  return request.post<AgentEvaluationListResponse>(`/agent_monitoring/traces/${traceId}/evaluate`)
}

// ---------- Phase 4: 数据导出 ----------

export function exportAgentTraces(format: 'json' | 'csv' = 'json') {
  return request.get(`/agent_monitoring/traces/export?format=${format}`, {
    responseType: 'blob',
  })
}

export function exportAgentEvaluations(format: 'json' | 'csv' = 'json') {
  return request.get(`/agent_monitoring/evaluations/export?format=${format}`, {
    responseType: 'blob',
  })
}
