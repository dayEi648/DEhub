import type { LucideIcon } from 'lucide-react'
import { ArrowRight } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
  minHeight?: number | string
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  minHeight = 300,
}: EmptyStateProps) {
  return (
    <div
      className="animate-fadeInUp"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        minHeight,
        padding: 'var(--spacing-xl) var(--spacing-md)',
        color: 'var(--color-muted)',
      }}
    >
      <div
        className="animate-float"
        style={{
          marginBottom: 'var(--spacing-md)',
          opacity: 0.35,
        }}
      >
        <Icon size={48} strokeWidth={1.2} />
      </div>
      <p
        style={{
          fontSize: 16,
          fontWeight: 500,
          color: 'var(--color-body)',
          margin: '0 0 var(--spacing-xs)',
        }}
      >
        {title}
      </p>
      {description && (
        <p
          style={{
            fontSize: 14,
            color: 'var(--color-muted-soft)',
            margin: '0 0 var(--spacing-md)',
            maxWidth: 320,
            lineHeight: 1.55,
          }}
        >
          {description}
        </p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="ripple-container"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            height: 40,
            padding: '0 20px',
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-primary)',
            color: 'var(--color-on-primary)',
            fontSize: 14,
            fontWeight: 500,
            border: 'none',
            cursor: 'pointer',
            transition: 'background-color 0.2s ease, transform 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-primary-active)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-primary)'
          }}
        >
          {action.label}
          <ArrowRight size={14} />
        </button>
      )}
    </div>
  )
}
