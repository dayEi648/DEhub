import { useState } from 'react'
import { Search, RotateCcw } from 'lucide-react'
import type { LogLevel } from '../types/systemLog'

export interface FilterState {
  level: LogLevel | ''
  is_resolved: '' | 'true' | 'false'
  module: string
  created_after: string
  created_before: string
}

interface LogFilterBarProps {
  filters: FilterState
  onChange: (filters: FilterState) => void
  onSearch: () => void
}

export default function LogFilterBar({ filters, onChange, onSearch }: LogFilterBarProps) {
  const [local, setLocal] = useState<FilterState>(filters)

  const update = (patch: Partial<FilterState>) => {
    const next = { ...local, ...patch }
    setLocal(next)
    onChange(next)
  }

  const reset = () => {
    const empty: FilterState = {
      level: '',
      is_resolved: '',
      module: '',
      created_after: '',
      created_before: '',
    }
    setLocal(empty)
    onChange(empty)
    onSearch()
  }

  const inputStyle: React.CSSProperties = {
    height: 40,
    padding: '10px 14px',
    borderRadius: 'var(--rounded-md)',
    border: '1px solid var(--color-hairline)',
    backgroundColor: 'var(--color-canvas)',
    color: 'var(--color-ink)',
    fontSize: 14,
    lineHeight: 1.4,
    minWidth: 140,
  }

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 'var(--spacing-md)',
        padding: 'var(--spacing-lg)',
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        marginBottom: 'var(--spacing-lg)',
      }}
    >
      {/* Level select */}
      <select
        style={inputStyle}
        value={local.level}
        onChange={(e) => update({ level: e.target.value as LogLevel | '' })}
      >
        <option value="">全部级别</option>
        <option value="WARN">WARN</option>
        <option value="ERROR">ERROR</option>
        <option value="CRITICAL">CRITICAL</option>
      </select>

      {/* Resolved select */}
      <select
        style={inputStyle}
        value={local.is_resolved}
        onChange={(e) => update({ is_resolved: e.target.value as '' | 'true' | 'false' })}
      >
        <option value="">全部状态</option>
        <option value="false">未处理</option>
        <option value="true">已处理</option>
      </select>

      {/* Module input */}
      <input
        type="text"
        placeholder="模块名称"
        style={{ ...inputStyle, minWidth: 180 }}
        value={local.module}
        onChange={(e) => update({ module: e.target.value })}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
      />

      {/* Date range */}
      <input
        type="datetime-local"
        style={inputStyle}
        value={local.created_after}
        onChange={(e) => update({ created_after: e.target.value })}
      />
      <span style={{ color: 'var(--color-muted)', fontSize: 13 }}>至</span>
      <input
        type="datetime-local"
        style={inputStyle}
        value={local.created_before}
        onChange={(e) => update({ created_before: e.target.value })}
      />

      <div style={{ marginLeft: 'auto', display: 'flex', gap: 'var(--spacing-sm)' }}>
        <button
          onClick={reset}
          style={{
            height: 40,
            padding: '0 16px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-canvas)',
            color: 'var(--color-ink)',
            border: '1px solid var(--color-hairline)',
            fontSize: 14,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <RotateCcw size={14} />
          重置
        </button>
        <button
          onClick={onSearch}
          style={{
            height: 40,
            padding: '0 20px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            fontSize: 14,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <Search size={14} />
          查询
        </button>
      </div>
    </div>
  )
}
