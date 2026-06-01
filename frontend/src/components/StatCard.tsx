interface StatCardProps {
  label: string
  value: number | string
  color?: string
  subValue?: string
}

export default function StatCard({ label, value, color, subValue }: StatCardProps) {
  const displayValue = typeof value === 'number' ? value.toLocaleString() : value
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        padding: 'var(--spacing-xl)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-xs)',
        minWidth: 160,
        flex: 1,
      }}
    >
      <span
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 36,
          fontWeight: 500,
          lineHeight: 1.1,
          color: color || 'var(--color-ink)',
          letterSpacing: '-0.5px',
        }}
      >
        {displayValue}
      </span>
      {subValue && (
        <span style={{ fontSize: 12, color: 'var(--color-muted)' }}>{subValue}</span>
      )}
      <span
        style={{
          fontSize: 13,
          fontWeight: 500,
          color: 'var(--color-muted)',
          lineHeight: 1.4,
        }}
      >
        {label}
      </span>
    </div>
  )
}
