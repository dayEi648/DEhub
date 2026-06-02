import { useCallback, useEffect, useState } from 'react'
import { Shield, RefreshCw, Eye, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import StatCard from '../../components/StatCard'
import type {
  ContentModerationRecord,
  ContentModerationStatsResponse,
  ModerationStatus,
  ModerationTargetType,
  RiskLevel,
} from '../../types/contentModeration'
import {
  getModerationRecords,
  getModerationStats,
  retryModerationRecord,
  exportModerationRecords,
} from '../../api/contentModeration'

const statusLabels: Record<ModerationStatus, string> = {
  pending: '待审核',
  running: '审核中',
  passed: '已通过',
  blocked: '已拦截',
  action_failed: '处置失败',
  review_failed: '审核失败',
  stale: '已过期',
}

const statusColors: Record<ModerationStatus, { bg: string; text: string }> = {
  pending: { bg: 'rgba(140, 140, 140, 0.12)', text: '#888' },
  running: { bg: 'rgba(99, 149, 214, 0.15)', text: '#4a7bb7' },
  passed: { bg: 'rgba(90, 170, 120, 0.12)', text: '#3d9e5f' },
  blocked: { bg: 'rgba(198, 69, 69, 0.12)', text: '#c64545' },
  action_failed: { bg: 'rgba(198, 69, 69, 0.18)', text: '#a83232' },
  review_failed: { bg: 'rgba(232, 165, 90, 0.15)', text: '#c4842a' },
  stale: { bg: 'rgba(140, 140, 140, 0.18)', text: '#666' },
}

const targetTypeLabels: Record<ModerationTargetType, string> = {
  user: '用户',
  blog_post: '博客',
  forum_zone: '论坛分区',
  forum_post: '论坛帖子',
  forum_reply: '论坛回复',
  comment: '评论',
}

const riskLevelLabels: Record<RiskLevel, string> = {
  none: '无',
  low: '低',
  medium: '中',
  high: '高',
}

const riskLevelColors: Record<RiskLevel, string> = {
  none: '#888',
  low: '#4a7bb7',
  medium: '#c4842a',
  high: '#c64545',
}

export default function ContentModerationList() {
  const navigate = useNavigate()
  const [records, setRecords] = useState<ContentModerationRecord[]>([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<ContentModerationStatsResponse | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(false)
  const [retryingId, setRetryingId] = useState<number | null>(null)

  // filters
  const [status, setStatus] = useState<ModerationStatus | ''>('')
  const [targetType, setTargetType] = useState<ModerationTargetType | ''>('')
  const [riskLevel, setRiskLevel] = useState<RiskLevel | ''>('')

  const fetchRecords = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...(status && { status }),
        ...(targetType && { target_type: targetType }),
        ...(riskLevel && { risk_level: riskLevel }),
      }
      const res = await getModerationRecords(params)
      setRecords(res.data.items)
      setTotal(res.data.total)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, status, targetType, riskLevel])

  const fetchStats = useCallback(async () => {
    try {
      const res = await getModerationStats()
      setStats(res.data)
    } catch {
      // handled by interceptor
    }
  }, [])

  useEffect(() => {
    fetchRecords()
  }, [fetchRecords])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  const handlePageChange = (p: number) => {
    if (p < 1) return
    setPage(p)
  }

  const handlePageSizeChange = (size: number) => {
    setPageSize(size)
    setPage(1)
  }

  const handleRetry = async (id: number) => {
    setRetryingId(id)
    try {
      await retryModerationRecord(id)
      fetchRecords()
      fetchStats()
    } catch {
      // handled by interceptor
    } finally {
      setRetryingId(null)
    }
  }

  const handleExport = async () => {
    try {
      const params = {
        ...(status && { status }),
        ...(targetType && { target_type: targetType }),
        ...(riskLevel && { risk_level: riskLevel }),
      }
      const res = await exportModerationRecords('json', params)
      const blob = new Blob([res.data])
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `content_moderation_${new Date().toISOString().slice(0, 10)}.json`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      // handled by interceptor
    }
  }

  const formatTime = (iso: string | null) => {
    if (!iso) return '-'
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const calcLatency = (record: ContentModerationRecord) => {
    if (!record.started_at || !record.finished_at) return '-'
    const ms = new Date(record.finished_at).getTime() - new Date(record.started_at).getTime()
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const totalPages = Math.ceil(total / pageSize) || 1

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
          <Shield size={24} color="var(--color-primary)" />
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
            内容审核
          </h1>
        </div>
        <button
          onClick={handleExport}
          style={{
            height: 36,
            padding: '0 16px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-canvas)',
            border: '1px solid var(--color-hairline)',
            color: 'var(--color-ink)',
            fontSize: 13,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            cursor: 'pointer',
          }}
        >
          <Download size={14} />
          导出数据
        </button>
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
        <StatCard label="审核总数" value={stats?.total ?? 0} />
        <StatCard label="今日审核" value={stats?.today_count ?? 0} color="var(--color-primary)" />
        <StatCard label="失败" value={stats?.failed_count ?? 0} color="var(--color-warning)" />
        <StatCard label="已拦截" value={stats?.blocked_count ?? 0} color="var(--color-error)" />
        <StatCard
          label="平均耗时"
          value={stats?.avg_latency_ms ? `${stats.avg_latency_ms}ms` : '-'}
          color="var(--color-accent-amber)"
        />
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--spacing-md)',
          marginBottom: 'var(--spacing-lg)',
          flexWrap: 'wrap',
          alignItems: 'center',
        }}
      >
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value as ModerationStatus); setPage(1) }}
          style={{
            height: 36,
            padding: '0 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            color: 'var(--color-ink)',
            fontSize: 13,
          }}
        >
          <option value="">全部状态</option>
          {Object.entries(statusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        <select
          value={targetType}
          onChange={(e) => { setTargetType(e.target.value as ModerationTargetType); setPage(1) }}
          style={{
            height: 36,
            padding: '0 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            color: 'var(--color-ink)',
            fontSize: 13,
          }}
        >
          <option value="">全部类型</option>
          {Object.entries(targetTypeLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        <select
          value={riskLevel}
          onChange={(e) => { setRiskLevel(e.target.value as RiskLevel); setPage(1) }}
          style={{
            height: 36,
            padding: '0 12px',
            borderRadius: 'var(--rounded-md)',
            border: '1px solid var(--color-hairline)',
            backgroundColor: 'var(--color-canvas)',
            color: 'var(--color-ink)',
            fontSize: 13,
          }}
        >
          <option value="">全部风险</option>
          {Object.entries(riskLevelLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div
        style={{
          backgroundColor: 'var(--color-surface-card)',
          borderRadius: 'var(--rounded-lg)',
          overflow: 'hidden',
        }}
      >
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-hairline)' }}>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>ID</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>对象</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>触发</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>状态</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>风险</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>模型</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>耗时</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>时间</th>
              <th style={{ width: 120, padding: '12px 16px', textAlign: 'right', color: 'var(--color-muted)', fontWeight: 500 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  加载中…
                </td>
              </tr>
            ) : records.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  暂无数据
                </td>
              </tr>
            ) : (
              records.map((record) => {
                const sColor = statusColors[record.status]
                return (
                  <tr
                    key={record.id}
                    style={{
                      borderBottom: '1px solid var(--color-hairline-soft)',
                      cursor: 'pointer',
                    }}
                    onClick={() => navigate(`/admin/content-moderation/${record.id}`)}
                  >
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>{record.id}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{ fontWeight: 500 }}>{targetTypeLabels[record.target_type]}</span>
                      <span style={{ color: 'var(--color-muted)', marginLeft: 4 }}>#{record.target_id}</span>
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-body)' }}>{record.trigger_action}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 10px',
                          borderRadius: 'var(--rounded-pill)',
                          fontSize: 12,
                          fontWeight: 600,
                          backgroundColor: sColor.bg,
                          color: sColor.text,
                        }}
                      >
                        {statusLabels[record.status]}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px' }}>
                      <span style={{ color: riskLevelColors[record.risk_level], fontWeight: 500 }}>
                        {riskLevelLabels[record.risk_level]}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>
                      {record.model_name || '-'}
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>
                      {calcLatency(record)}
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>
                      {formatTime(record.created_at)}
                    </td>
                    <td style={{ padding: '10px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            navigate(`/admin/content-moderation/${record.id}`)
                          }}
                          title="查看详情"
                          style={{
                            width: 28,
                            height: 28,
                            borderRadius: 'var(--rounded-sm)',
                            backgroundColor: 'var(--color-canvas)',
                            border: '1px solid var(--color-hairline)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--color-muted)',
                            cursor: 'pointer',
                          }}
                        >
                          <Eye size={14} />
                        </button>
                        {(record.status === 'review_failed' || record.status === 'action_failed' || record.status === 'stale') && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRetry(record.id)
                            }}
                            disabled={retryingId === record.id}
                            title="重试审核"
                            style={{
                              width: 28,
                              height: 28,
                              borderRadius: 'var(--rounded-sm)',
                              backgroundColor: 'var(--color-canvas)',
                              border: '1px solid var(--color-hairline)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'var(--color-primary)',
                              cursor: retryingId === record.id ? 'not-allowed' : 'pointer',
                              opacity: retryingId === record.id ? 0.6 : 1,
                            }}
                          >
                            <RefreshCw size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })
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
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', fontSize: 13, color: 'var(--color-muted)' }}>
          <span>每页</span>
          <select
            value={pageSize}
            onChange={(e) => handlePageSizeChange(Number(e.target.value))}
            style={{
              height: 32,
              padding: '0 8px',
              borderRadius: 'var(--rounded-sm)',
              border: '1px solid var(--color-hairline)',
              backgroundColor: 'var(--color-canvas)',
              color: 'var(--color-ink)',
              fontSize: 13,
            }}
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span>条</span>
          <span style={{ marginLeft: 8 }}>共 {total.toLocaleString()} 条</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <button
            onClick={() => handlePageChange(page - 1)}
            disabled={page <= 1}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-sm)',
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: page <= 1 ? 'var(--color-muted-soft)' : 'var(--color-ink)',
              cursor: page <= 1 ? 'not-allowed' : 'pointer',
            }}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={{ fontSize: 13, color: 'var(--color-muted)', minWidth: 80, textAlign: 'center' }}>
            {page} / {totalPages}
          </span>
          <button
            onClick={() => handlePageChange(page + 1)}
            disabled={page >= totalPages}
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-sm)',
              backgroundColor: 'var(--color-canvas)',
              border: '1px solid var(--color-hairline)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: page >= totalPages ? 'var(--color-muted-soft)' : 'var(--color-ink)',
              cursor: page >= totalPages ? 'not-allowed' : 'pointer',
            }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
