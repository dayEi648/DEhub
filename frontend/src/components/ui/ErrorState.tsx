import { RefreshCw, AlertTriangle } from 'lucide-react'

interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  minHeight?: number | string
}

export default function ErrorState({
  title = '加载失败',
  description = '请检查网络连接后重试',
  onRetry,
  minHeight = 300,
}: ErrorStateProps) {
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
        color: 'var(--color-error)',
      }}
    >
      <div
        className="animate-shake"
        style={{
          marginBottom: 'var(--spacing-md)',
          opacity: 0.6,
        }}
      >
        <AlertTriangle size={48} strokeWidth={1.2} />
      </div>
      <p
        style={{
          fontSize: 16,
          fontWeight: 500,
          color: 'var(--color-body-strong)',
          margin: '0 0 var(--spacing-xs)',
        }}
      >
        {title}
      </p>
      <p
        style={{
          fontSize: 14,
          color: 'var(--color-muted)',
          margin: '0 0 var(--spacing-md)',
          maxWidth: 320,
          lineHeight: 1.55,
        }}
      >
        {description}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
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
            e.currentTarget.style.transform = 'scale(1.02)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-primary)'
            e.currentTarget.style.transform = 'scale(1)'
          }}
        >
          <RefreshCw size={14} />
          重新加载
        </button>
      )}
    </div>
  )
}
