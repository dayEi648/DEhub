import { Sparkles } from 'lucide-react'

export default function Footer() {
  return (
    <footer
      style={{
        backgroundColor: 'var(--color-surface-dark)',
        color: 'var(--color-on-dark-soft)',
        padding: 'var(--spacing-xl) var(--spacing-xl)',
        marginTop: 'auto',
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--spacing-md)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
          <Sparkles size={16} color="var(--color-on-dark)" />
          <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, color: 'var(--color-on-dark)' }}>DE hub</span>
        </div>
        <span style={{ fontSize: 13, color: 'var(--color-on-dark-soft)' }}>
          © {new Date().getFullYear()} Developer Space. All rights reserved.
        </span>
      </div>
    </footer>
  )
}
