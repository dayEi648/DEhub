import { Construction } from 'lucide-react'

export default function PlaceholderPage() {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-section)',
        color: 'var(--color-muted)',
      }}
    >
      <Construction size={48} strokeWidth={1.2} style={{ marginBottom: 'var(--spacing-lg)', opacity: 0.6 }} />
      <h2
        style={{
          fontFamily: 'var(--font-display)',
          fontSize: 28,
          fontWeight: 400,
          color: 'var(--color-ink)',
          margin: '0 0 var(--spacing-sm)',
          letterSpacing: '-0.3px',
        }}
      >
        功能开发中
      </h2>
      <p style={{ fontSize: 14, color: 'var(--color-muted)', margin: 0 }}>
        该模块尚未开放，敬请期待
      </p>
    </div>
  )
}
