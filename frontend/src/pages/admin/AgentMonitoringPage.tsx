import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, AlertTriangle, BarChart3, ChevronLeft, ChevronRight, Download } from 'lucide-react'
import StatCard from '../../components/StatCard'
import { exportAgentTraces, getAgentTraces, getAgentTraceStats } from '../../api/agentMonitoring'
import type { AgentTrace, AgentTraceStatsResponse } from '../../types/agentMonitoring'

const PAGE_SIZE_OPTIONS = [10, 20, 50]
const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'completed', label: '成功' },
  { value: 'failed', label: '失败' },
  { value: 'started', label: '进行中' },
]

function formatDuration(ms: number | null): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

function truncateText(text: string | null, maxLen: number = 60): string {
  if (!text) return '-'
  return text.length > maxLen ? text.slice(0, maxLen) + '...' : text
}

export default function AgentMonitoringPage() {
  const [traces, setTraces] = useState<AgentTrace[]>([])
  const [total, setTotal] = useState(0)
  const navigate = useNavigate()
  const [stats, setStats] = useState<AgentTraceStatsResponse | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [statusFilter, setStatusFilter] = useState('')
  const [flaggedFilter, setFlaggedFilter] = useState<boolean | undefined>(undefined)
  const [loading, setLoading] = useState(false)

  const fetchTraces = useCallback(async () => {
    setLoading(true)
    try {
      const res = await getAgentTraces({
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...(statusFilter ? { status: statusFilter } : {}),
        ...(flaggedFilter !== undefined ? { is_flagged: flaggedFilter } : {}),
      })
      setTraces(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, statusFilter, flaggedFilter])

  const fetchStats = useCallback(async () => {
    try {
      const res = await getAgentTraceStats()
      setStats(res.data)
    } catch {
      // handled by interceptor
    }
  }, [])

  useEffect(() => {
    fetchTraces()
  }, [fetchTraces])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%' }}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--spacing-xl)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <Activity size={24} color="var(--color-primary)" />
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: 28,
              fontWeight: 400,
              margin: 0,
              color: 'var(--color-ink)',
              letterSpacing: '-0.3px',
            }}
          >
            Agent 监控
          </h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={async () => {
              try {
                const res = await exportAgentTraces('csv')
                const blob = new Blob([res.data], { type: 'text/csv' })
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `agent_traces_${new Date().toISOString().slice(0, 19).replace(/:/g, '')}.csv`
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
            导出 CSV
          </button>
          <button
            onClick={() => navigate('/admin/agent-monitoring/dashboard')}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--rounded-md)',
              border: '1px solid var(--color-hairline)',
              backgroundColor: 'var(--color-canvas)',
              fontSize: 13,
              fontWeight: 500,
              color: 'var(--color-primary)',
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
            <BarChart3 size={16} />
            质量仪表盘
          </button>
        </div>
      </div>

      {/* Stats */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-lg)',
          marginBottom: 'var(--spacing-xl)',
          flexWrap: 'wrap',
        }}
      >
        <StatCard label="总调用数" value={stats?.total ?? 0} />
        <StatCard label="今日调用" value={stats?.today_count ?? 0} color="var(--color-accent-teal)" />
        <StatCard label="失败次数" value={stats?.failed_count ?? 0} color="var(--color-error)" />
        <StatCard label="平均延迟(ms)" value={stats?.avg_latency_ms ?? 0} color="var(--color-accent-amber)" />
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-lg)',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value)
            setPage(1)
          }}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            fontSize: 14,
            color: 'var(--color-ink)',
            cursor: 'pointer',
          }}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={flaggedFilter === undefined ? '' : String(flaggedFilter)}
          onChange={(e) => {
            const val = e.target.value
            setFlaggedFilter(val === '' ? undefined : val === 'true')
            setPage(1)
          }}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            fontSize: 14,
            color: 'var(--color-ink)',
            cursor: 'pointer',
          }}
        >
          <option value="">全部标记</option>
          <option value="true">仅看异常</option>
          <option value="false">仅看正常</option>
        </select>

        <span style={{ fontSize: 13, color: 'var(--color-muted)', marginLeft: 'auto' }}>
          共 {total} 条记录
        </span>
      </div>

      {/* Table */}
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: 'var(--rounded-lg)',
          border: '1px solid var(--color-hairline)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
          <thead>
            <tr style={{ backgroundColor: 'var(--color-surface-soft)' }}>
              <th style={thStyle}>Trace ID</th>
              <th style={thStyle}>用户</th>
              <th style={thStyle}>输入</th>
              <th style={thStyle}>状态</th>
              <th style={thStyle}>标记</th>
              <th style={thStyle}>耗时</th>
              <th style={thStyle}>Token</th>
              <th style={thStyle}>步数</th>
              <th style={thStyle}>工具</th>
              <th style={thStyle}>时间</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} style={tdStyleCenter}>
                  加载中...
                </td>
              </tr>
            ) : traces.length === 0 ? (
              <tr>
                <td colSpan={10} style={tdStyleCenter}>
                  暂无数据
                </td>
              </tr>
            ) : (
              traces.map((trace) => (
                <tr
                  key={trace.id}
                  onClick={() => navigate(`/admin/agent-monitoring/${trace.trace_id}`)}
                  style={{
                    borderBottom: '1px solid var(--color-hairline-soft)',
                    transition: 'background-color 150ms ease',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent'
                  }}
                >
                  <td style={tdStyle}>
                    <code style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                      {trace.trace_id}
                    </code>
                  </td>
                  <td style={tdStyle}>{trace.user_id ?? '-'}</td>
                  <td style={tdStyle} title={trace.input_message || ''}>
                    {truncateText(trace.input_message)}
                  </td>
                  <td style={tdStyle}>
                    <StatusBadge status={trace.status} />
                  </td>
                  <td style={tdStyle}>
                    {trace.is_flagged ? (
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          fontSize: 12,
                          fontWeight: 500,
                          color: 'var(--color-error)',
                          backgroundColor: 'rgba(198, 69, 69, 0.12)',
                          padding: '2px 8px',
                          borderRadius: 'var(--rounded-pill)',
                        }}
                      >
                        <AlertTriangle size={12} />
                        异常
                      </span>
                    ) : (
                      <span style={{ fontSize: 12, color: 'var(--color-muted-soft)' }}>-</span>
                    )}
                  </td>
                  <td style={tdStyle}>{formatDuration(trace.latency_ms)}</td>
                  <td style={tdStyle}>{trace.total_tokens ?? '-'}</td>
                  <td style={tdStyle}>{trace.node_steps}</td>
                  <td style={tdStyle}>{trace.tool_calls_count}</td>
                  <td style={tdStyle}>
                    <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>
                      {trace.started_at ? new Date(trace.started_at).toLocaleString() : '-'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 'var(--spacing-lg)',
          flexWrap: 'wrap',
          gap: 'var(--spacing-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: 'var(--color-muted)' }}>每页</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value))
              setPage(1)
            }}
            style={{
              padding: '4px 8px',
              borderRadius: 'var(--rounded-md)',
              border: '1px solid var(--color-hairline)',
              backgroundColor: 'var(--color-canvas)',
              fontSize: 13,
            }}
          >
            {PAGE_SIZE_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            style={pageBtnStyle(page <= 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={{ fontSize: 13, color: 'var(--color-muted)' }}>
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            style={pageBtnStyle(page >= totalPages)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    completed: 'var(--color-success)',
    failed: 'var(--color-error)',
    started: 'var(--color-accent-amber)',
  }
  const bgMap: Record<string, string> = {
    completed: 'rgba(93, 184, 114, 0.12)',
    failed: 'rgba(198, 69, 69, 0.12)',
    started: 'rgba(232, 165, 90, 0.12)',
  }
  const labelMap: Record<string, string> = {
    completed: '成功',
    failed: '失败',
    started: '进行中',
  }
  const color = colorMap[status] || 'var(--color-muted)'
  const bg = bgMap[status] || 'var(--color-surface-soft)'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 'var(--rounded-pill)',
        fontSize: 12,
        fontWeight: 500,
        color,
        backgroundColor: bg,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          backgroundColor: color,
        }}
      />
      {labelMap[status] || status}
    </span>
  )
}

const thStyle: React.CSSProperties = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: 13,
  fontWeight: 500,
  color: 'var(--color-muted)',
  borderBottom: '1px solid var(--color-hairline)',
  whiteSpace: 'nowrap',
}

const tdStyle: React.CSSProperties = {
  padding: '12px 16px',
  color: 'var(--color-body)',
  fontSize: 13,
  maxWidth: 200,
  overflow: 'hidden',
  textOverflow: 'ellipsis',
  whiteSpace: 'nowrap',
}

const tdStyleCenter: React.CSSProperties = {
  padding: '32px 16px',
  textAlign: 'center',
  color: 'var(--color-muted)',
  fontSize: 14,
}

function pageBtnStyle(disabled: boolean): React.CSSProperties {
  return {
    width: 28,
    height: 28,
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.5 : 1,
    color: 'var(--color-ink)',
  }
}
