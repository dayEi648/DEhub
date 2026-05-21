import { useState } from 'react'
import { Eye, CheckCircle, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'
import type { SystemLog, LogLevel } from '../types/systemLog'

interface LogTableProps {
  logs: SystemLog[]
  total: number
  page: number
  pageSize: number
  loading: boolean
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  onView: (log: SystemLog) => void
  onResolve: (id: number) => void
  onDelete: (id: number) => void
  onBatchResolve: (ids: number[]) => void
}

const levelColors: Record<LogLevel, { bg: string; text: string }> = {
  WARN: { bg: 'rgba(232, 165, 90, 0.15)', text: '#d4a017' },
  ERROR: { bg: 'rgba(198, 69, 69, 0.12)', text: '#c64545' },
  CRITICAL: { bg: '#c64545', text: '#ffffff' },
}

export default function LogTable({
  logs,
  total,
  page,
  pageSize,
  loading,
  onPageChange,
  onPageSizeChange,
  onView,
  onResolve,
  onDelete,
  onBatchResolve,
}: LogTableProps) {
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const totalPages = Math.ceil(total / pageSize) || 1

  const toggleSelect = (id: number) => {
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const toggleSelectAll = () => {
    if (selected.size === logs.length && logs.length > 0) {
      setSelected(new Set())
    } else {
      setSelected(new Set(logs.map((l) => l.id)))
    }
  }

  const handleBatchResolve = () => {
    const ids = Array.from(selected)
    if (ids.length === 0) return
    if (confirm(`确定要将选中的 ${ids.length} 条日志标记为已处理吗？`)) {
      onBatchResolve(ids)
      setSelected(new Set())
    }
  }

  const formatTime = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const truncate = (s: string, max = 60) =>
    s.length > max ? s.slice(0, max) + '…' : s

  return (
    <div>
      {/* Batch actions */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 'var(--spacing-md)',
          minHeight: 36,
        }}
      >
        <span style={{ fontSize: 13, color: 'var(--color-muted)' }}>
          共 {total.toLocaleString()} 条记录
          {selected.size > 0 && (
            <span style={{ color: 'var(--color-primary)', marginLeft: 8 }}>
              已选择 {selected.size} 条
            </span>
          )}
        </span>
        {selected.size > 0 && (
          <button
            onClick={handleBatchResolve}
            style={{
              height: 32,
              padding: '0 14px',
              borderRadius: 'var(--rounded-md)',
              backgroundColor: 'var(--color-success)',
              color: '#fff',
              fontSize: 13,
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <CheckCircle size={14} />
            批量标记已处理
          </button>
        )}
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
              <th style={{ width: 40, padding: '12px 16px', textAlign: 'left' }}>
                <input
                  type="checkbox"
                  checked={logs.length > 0 && selected.size === logs.length}
                  onChange={toggleSelectAll}
                />
              </th>
              <th style={{ width: 60, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>ID</th>
              <th style={{ width: 90, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>级别</th>
              <th style={{ width: 120, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>模块</th>
              <th style={{ padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>消息</th>
              <th style={{ width: 160, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>创建时间</th>
              <th style={{ width: 80, padding: '12px 8px', textAlign: 'left', color: 'var(--color-muted)', fontWeight: 500 }}>状态</th>
              <th style={{ width: 130, padding: '12px 16px', textAlign: 'right', color: 'var(--color-muted)', fontWeight: 500 }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={8} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  加载中…
                </td>
              </tr>
            ) : logs.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ padding: 'var(--spacing-xxl)', textAlign: 'center', color: 'var(--color-muted)' }}>
                  暂无数据
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const colors = levelColors[log.level]
                return (
                  <tr
                    key={log.id}
                    style={{
                      borderBottom: '1px solid var(--color-hairline-soft)',
                      backgroundColor: selected.has(log.id) ? 'var(--color-surface-soft)' : 'transparent',
                    }}
                  >
                    <td style={{ padding: '10px 16px' }}>
                      <input
                        type="checkbox"
                        checked={selected.has(log.id)}
                        onChange={() => toggleSelect(log.id)}
                      />
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>{log.id}</td>
                    <td style={{ padding: '10px 8px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 10px',
                          borderRadius: 'var(--rounded-pill)',
                          fontSize: 12,
                          fontWeight: 600,
                          backgroundColor: colors.bg,
                          color: colors.text,
                        }}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-body)' }}>{log.module || '-'}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-ink)', maxWidth: 360 }}>
                      <span title={log.message}>{truncate(log.message)}</span>
                    </td>
                    <td style={{ padding: '10px 8px', color: 'var(--color-muted)' }}>{formatTime(log.created_at)}</td>
                    <td style={{ padding: '10px 8px' }}>
                      {log.is_resolved ? (
                        <span style={{ color: 'var(--color-success)', fontWeight: 500 }}>已处理</span>
                      ) : (
                        <span style={{ color: 'var(--color-warning)', fontWeight: 500 }}>未处理</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        <button
                          onClick={() => onView(log)}
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
                          }}
                        >
                          <Eye size={14} />
                        </button>
                        {!log.is_resolved && (
                          <button
                            onClick={() => onResolve(log.id)}
                            title="标记已处理"
                            style={{
                              width: 28,
                              height: 28,
                              borderRadius: 'var(--rounded-sm)',
                              backgroundColor: 'var(--color-canvas)',
                              border: '1px solid var(--color-hairline)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: 'var(--color-success)',
                            }}
                          >
                            <CheckCircle size={14} />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            if (confirm('确定删除这条日志吗？')) onDelete(log.id)
                          }}
                          title="删除"
                          style={{
                            width: 28,
                            height: 28,
                            borderRadius: 'var(--rounded-sm)',
                            backgroundColor: 'var(--color-canvas)',
                            border: '1px solid var(--color-hairline)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'var(--color-error)',
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
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
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
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
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <button
            onClick={() => onPageChange(page - 1)}
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
            onClick={() => onPageChange(page + 1)}
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
