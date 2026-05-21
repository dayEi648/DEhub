import { useCallback, useEffect, useState } from 'react'
import { ScrollText } from 'lucide-react'
import StatCard from '../../components/StatCard'
import LogFilterBar, { type FilterState } from '../../components/LogFilterBar'
import LogTable from '../../components/LogTable'
import LogDetailModal from '../../components/LogDetailModal'
import {
  getLogList,
  getLogStats,
  batchResolveLogs,
  resolveLog,
  deleteLog,
} from '../../api/systemLogs'
import type { SystemLog, SystemLogStatsResponse } from '../../types/systemLog'

const emptyFilters: FilterState = {
  level: '',
  is_resolved: '',
  module: '',
  created_after: '',
  created_before: '',
}

export default function LogManagement() {
  const [logs, setLogs] = useState<SystemLog[]>([])
  const [total, setTotal] = useState(0)
  const [stats, setStats] = useState<SystemLogStatsResponse | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [filters, setFilters] = useState<FilterState>(emptyFilters)
  const [loading, setLoading] = useState(false)
  const [detailLog, setDetailLog] = useState<SystemLog | null>(null)

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...(filters.level && { level: filters.level }),
        ...(filters.is_resolved && { is_resolved: filters.is_resolved === 'true' }),
        ...(filters.module && { module: filters.module }),
        ...(filters.created_after && { created_after: new Date(filters.created_after).toISOString() }),
        ...(filters.created_before && { created_before: new Date(filters.created_before).toISOString() }),
      }
      const res = await getLogList(params)
      setLogs(res.data.items)
      setTotal(res.data.total)
    } catch {
      // handled by interceptor
    } finally {
      setLoading(false)
    }
  }, [page, pageSize, filters])

  const fetchStats = useCallback(async () => {
    try {
      const res = await getLogStats()
      setStats(res.data)
    } catch {
      // handled by interceptor
    }
  }, [])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

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

  const handleResolve = async (id: number) => {
    try {
      await resolveLog(id)
      fetchLogs()
      fetchStats()
    } catch {
      // handled by interceptor
    }
  }

  const handleBatchResolve = async (ids: number[]) => {
    try {
      await batchResolveLogs(ids)
      fetchLogs()
      fetchStats()
    } catch {
      // handled by interceptor
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteLog(id)
      fetchLogs()
      fetchStats()
    } catch {
      // handled by interceptor
    }
  }

  return (
    <div style={{ padding: 'var(--spacing-xl)', width: '100%' }}>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-sm)',
          marginBottom: 'var(--spacing-xl)',
        }}
      >
        <ScrollText size={24} color="var(--color-primary)" />
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
          日志管理
        </h1>
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
        <StatCard label="日志总数" value={stats?.total ?? 0} />
        <StatCard label="未处理" value={stats?.total_unresolved ?? 0} color="var(--color-warning)" />
        <StatCard label="WARN" value={stats?.warn_count ?? 0} color="var(--color-accent-amber)" />
        <StatCard label="ERROR" value={stats?.error_count ?? 0} color="var(--color-error)" />
        <StatCard label="CRITICAL" value={stats?.critical_count ?? 0} color="#a82828" />
      </div>

      {/* Filters */}
      <LogFilterBar
        filters={filters}
        onChange={setFilters}
        onSearch={() => setPage(1)}
      />

      {/* Table */}
      <LogTable
        logs={logs}
        total={total}
        page={page}
        pageSize={pageSize}
        loading={loading}
        onPageChange={handlePageChange}
        onPageSizeChange={handlePageSizeChange}
        onView={setDetailLog}
        onResolve={handleResolve}
        onDelete={handleDelete}
        onBatchResolve={handleBatchResolve}
      />

      {/* Detail Modal */}
      {detailLog && (
        <LogDetailModal
          log={detailLog}
          onClose={() => setDetailLog(null)}
          onResolve={handleResolve}
        />
      )}
    </div>
  )
}
