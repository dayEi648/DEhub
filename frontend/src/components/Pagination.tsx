import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  current: number
  total: number
  onChange: (page: number) => void
}

export default function Pagination({ current, total, onChange }: PaginationProps) {
  if (total <= 1) return null

  const pages: (number | string)[] = []
  const maxVisible = 5

  if (total <= maxVisible + 2) {
    for (let i = 1; i <= total; i++) pages.push(i)
  } else {
    pages.push(1)
    if (current > 3) pages.push('...')
    const start = Math.max(2, current - 1)
    const end = Math.min(total - 1, current + 1)
    for (let i = start; i <= end; i++) pages.push(i)
    if (current < total - 2) pages.push('...')
    pages.push(total)
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--spacing-xs)', marginTop: 'var(--spacing-xl)' }}>
      <button
        onClick={() => onChange(current - 1)}
        disabled={current === 1}
        style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: current === 1 ? 'not-allowed' : 'pointer',
          opacity: current === 1 ? 0.5 : 1,
          color: 'var(--color-ink)',
          transition: 'all 150ms ease',
        }}
      >
        <ChevronLeft size={16} />
      </button>

      {pages.map((p, idx) =>
        p === '...' ? (
          <span key={`dot-${idx}`} style={{ padding: '0 8px', color: 'var(--color-muted-soft)', fontSize: 14 }}>
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onChange(p as number)}
            style={{
              minWidth: 36,
              height: 36,
              borderRadius: 'var(--rounded-md)',
              border: '1px solid',
              borderColor: current === p ? 'var(--color-primary)' : 'var(--color-hairline)',
              backgroundColor: current === p ? 'var(--color-primary)' : 'var(--color-canvas)',
              color: current === p ? 'var(--color-on-primary)' : 'var(--color-ink)',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 150ms ease',
            }}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onChange(current + 1)}
        disabled={current === total}
        style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--rounded-md)',
          border: '1px solid var(--color-hairline)',
          backgroundColor: 'var(--color-canvas)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: current === total ? 'not-allowed' : 'pointer',
          opacity: current === total ? 0.5 : 1,
          color: 'var(--color-ink)',
          transition: 'all 150ms ease',
        }}
      >
        <ChevronRight size={16} />
      </button>
    </div>
  )
}
