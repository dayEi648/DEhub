import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart3,
  ChevronLeft,
  TrendingDown,
  AlertTriangle,
  Download,
} from 'lucide-react'
import StatCard from '../../components/StatCard'
import {
  exportAgentEvaluations,
  getAgentEvaluationStats,
  getAgentEvaluationTrend,
  getAgentEvaluations,
  getAgentTraceStats,
} from '../../api/agentMonitoring'
import type {
  AgentEvaluation,
  AgentEvaluationStatsResponse,
  AgentTraceStatsResponse,
} from '../../types/agentMonitoring'

const DIMENSION_LABELS: Record<string, string> = {
  relevance: '相关性',
  helpfulness: '有用性',
  coherence: '连贯性',
  tool_accuracy: '工具成功率',
}

const DIMENSION_COLORS: Record<string, string> = {
  relevance: 'var(--color-primary)',
  helpfulness: 'var(--color-accent-teal)',
  coherence: 'var(--color-accent-amber)',
  tool_accuracy: 'var(--color-success)',
}

export default function AgentMonitoringDashboard() {
  const navigate = useNavigate()
  const [traceStats, setTraceStats] = useState<AgentTraceStatsResponse | null>(null)
  const [evalStats, setEvalStats] = useState<AgentEvaluationStatsResponse | null>(null)
  const [trend, setTrend] = useState<Array<{ date: string; count: number; avg_score: number }>>([])
  const [lowScores, setLowScores] = useState<AgentEvaluation[]>([])
  const [loading, setLoading] = useState(false)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [tsRes, esRes, trRes, lsRes] = await Promise.all([
        getAgentTraceStats(),
        getAgentEvaluationStats(),
        getAgentEvaluationTrend(7),
        getAgentEvaluations({ max_score: 0.5, limit: 20 }),
      ])
      setTraceStats(tsRes.data)
      setEvalStats(esRes.data)
      setTrend(trRes.data.items || [])
      setLowScores(lsRes.data.items || [])
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const avgScorePercent = evalStats
    ? Math.round((evalStats.avg_score || 0) * 100)
    : 0

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-xl)',
        }}
      >
        <button
          onClick={() => navigate('/admin/agent-monitoring')}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 32,
            height: 32,
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            cursor: 'pointer',
            color: 'var(--color-ink)',
          }}
        >
          <ChevronLeft size={18} />
        </button>
        <BarChart3 size={24} color="var(--color-primary)" />
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28,
            fontWeight: 400,
            margin: 0,
            color: 'var(--color-ink)',
            letterSpacing: '-0.3px',
            flex: 1,
          }}
        >
          质量仪表盘
        </h1>
        <button
          onClick={async () => {
            try {
              const res = await exportAgentEvaluations('csv')
              const blob = new Blob([res.data], { type: 'text/csv' })
              const url = window.URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `agent_evaluations_${new Date().toISOString().slice(0, 19).replace(/:/g, '')}.csv`
              a.click()
              window.URL.revokeObjectURL(url)
            } catch {
              // handled by interceptor
            }
          }}
          style={{
            padding: '8px 16px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            transition: 'all 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
          }}
        >
          <Download size={16} />
          导出评估 CSV
        </button>
      </div>

      {/* Stats Cards */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-lg)',
          marginBottom: 'var(--spacing-xl)',
          flexWrap: 'wrap',
        }}
      >
        <StatCard
          label="总评估数"
          value={evalStats?.total_evaluations ?? 0}
          color="var(--color-primary)"
        />
        <StatCard
          label="平均评分"
          value={`${avgScorePercent}%`}
          color={avgScorePercent >= 70 ? 'var(--color-success)' : avgScorePercent >= 40 ? 'var(--color-accent-amber)' : 'var(--color-error)'}
          subValue={evalStats ? `基于 ${evalStats.total_evaluations} 次评估` : undefined}
        />
        <StatCard
          label="低评分数 (&lt;0.5)"
          value={evalStats?.low_score_count ?? 0}
          color="var(--color-error)"
        />
        <StatCard
          label="今日调用"
          value={traceStats?.today_count ?? 0}
          color="var(--color-accent-teal)"
        />
        <StatCard
          label="平均延迟"
          value={`${traceStats?.avg_latency_ms ?? 0}ms`}
          color="var(--color-muted)"
        />
        <StatCard
          label="失败次数"
          value={traceStats?.failed_count ?? 0}
          color="var(--color-error)"
        />
      </div>

      {loading && (
        <div style={{ padding: 32, textAlign: 'center', color: 'var(--color-muted)' }}>
          加载中...
        </div>
      )}

      {/* Two Column Layout */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
          gap: 'var(--spacing-xl)',
        }}
      >
        {/* Dimension Distribution */}
        <div
          style={{
            backgroundColor: 'var(--color-canvas)',
            borderRadius: 'var(--rounded-lg)',
            border: '1px solid var(--color-hairline)',
            padding: 'var(--spacing-xl)',
          }}
        >
          <h2
            style={{
              fontSize: 16,
              fontWeight: 500,
              margin: '0 0 var(--spacing-lg)',
              color: 'var(--color-ink)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <BarChart3 size={18} color="var(--color-primary)" />
            维度评分分布
          </h2>

          {evalStats && evalStats.dimension_avgs.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {evalStats.dimension_avgs.map((d) => {
                const pct = Math.round((d.avg_score || 0) * 100)
                const color = DIMENSION_COLORS[d.dimension] || 'var(--color-primary)'
                return (
                  <div key={d.dimension}>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        fontSize: 13,
                        marginBottom: 4,
                        color: 'var(--color-body)',
                      }}
                    >
                      <span>{DIMENSION_LABELS[d.dimension] || d.dimension}</span>
                      <span style={{ fontWeight: 500 }}>{pct}%</span>
                    </div>
                    <div
                      style={{
                        width: '100%',
                        height: 8,
                        backgroundColor: 'var(--color-surface-soft)',
                        borderRadius: 'var(--rounded-pill)',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          backgroundColor: color,
                          borderRadius: 'var(--rounded-pill)',
                          transition: 'width 500ms ease',
                        }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div style={{ color: 'var(--color-muted)', fontSize: 14, padding: '16px 0' }}>
              暂无评估数据
            </div>
          )}
        </div>

        {/* Trend */}
        <div
          style={{
            backgroundColor: 'var(--color-canvas)',
            borderRadius: 'var(--rounded-lg)',
            border: '1px solid var(--color-hairline)',
            padding: 'var(--spacing-xl)',
          }}
        >
          <h2
            style={{
              fontSize: 16,
              fontWeight: 500,
              margin: '0 0 var(--spacing-lg)',
              color: 'var(--color-ink)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <TrendingDown size={18} color="var(--color-accent-teal)" />
            近7日趋势
          </h2>

          {trend.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
                  <th style={{ ...thStyle, textAlign: 'left' }}>日期</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>评估数</th>
                  <th style={{ ...thStyle, textAlign: 'right' }}>平均评分</th>
                </tr>
              </thead>
              <tbody>
                {trend.map((row) => (
                  <tr key={row.date} style={{ borderBottom: '1px solid var(--color-hairline-soft)' }}>
                    <td style={{ ...tdStyle, textAlign: 'left' }}>{row.date}</td>
                    <td style={{ ...tdStyle, textAlign: 'right' }}>{row.count}</td>
                    <td style={{ ...tdStyle, textAlign: 'right' }}>
                      <span
                        style={{
                          color:
                            row.avg_score >= 0.7
                              ? 'var(--color-success)'
                              : row.avg_score >= 0.4
                                ? 'var(--color-accent-amber)'
                                : 'var(--color-error)',
                          fontWeight: 500,
                        }}
                      >
                        {Math.round(row.avg_score * 100)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ color: 'var(--color-muted)', fontSize: 14, padding: '16px 0' }}>
              暂无趋势数据
            </div>
          )}
        </div>
      </div>

      {/* Low Score List */}
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          border: '1px solid var(--color-hairline)',
          padding: 'var(--spacing-xl)',
          marginTop: 'var(--spacing-xl)',
        }}
      >
        <h2
          style={{
            fontSize: 16,
            fontWeight: 500,
            margin: '0 0 var(--spacing-lg)',
            color: 'var(--color-ink)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <AlertTriangle size={18} color="var(--color-error)" />
          低评分记录（&lt; 0.5）
        </h2>

        {lowScores.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-hairline)', backgroundColor: 'var(--color-surface-soft)' }}>
                <th style={thStyle}>Trace ID</th>
                <th style={thStyle}>维度</th>
                <th style={thStyle}>评分</th>
                <th style={thStyle}>理由</th>
                <th style={thStyle}>时间</th>
              </tr>
            </thead>
            <tbody>
              {lowScores.map((item) => (
                <tr
                  key={item.id}
                  style={{
                    borderBottom: '1px solid var(--color-hairline-soft)',
                    cursor: 'pointer',
                  }}
                  onClick={() => navigate(`/admin/agent-monitoring/${item.trace_id}`)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <td style={tdStyle}>
                    <code style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                      {item.trace_id}
                    </code>
                  </td>
                  <td style={tdStyle}>
                    {DIMENSION_LABELS[item.dimension] || item.dimension}
                  </td>
                  <td style={tdStyle}>
                    <span
                      style={{
                        color: 'var(--color-error)',
                        fontWeight: 600,
                      }}
                    >
                      {Math.round(item.score * 100)}%
                    </span>
                  </td>
                  <td style={{ ...tdStyle, maxWidth: 300 }} title={item.reason || ''}>
                    {item.reason || '-'}
                  </td>
                  <td style={tdStyle}>
                    <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                      {item.evaluated_at
                        ? new Date(item.evaluated_at).toLocaleString()
                        : '-'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ color: 'var(--color-muted)', fontSize: 14, padding: '16px 0' }}>
            暂无低评分记录
          </div>
        )}
      </div>
    </div>
  )
}

const thStyle: React.CSSProperties = {
  padding: '10px 12px',
  textAlign: 'left',
  fontSize: 12,
  fontWeight: 500,
  color: 'var(--color-muted)',
  whiteSpace: 'nowrap',
}

const tdStyle: React.CSSProperties = {
  padding: '10px 12px',
  color: 'var(--color-body)',
  fontSize: 13,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
}
