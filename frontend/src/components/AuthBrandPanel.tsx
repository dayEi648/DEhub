export default function AuthBrandPanel({ slogan }: { slogan: string }) {
  return (
    <div
      className="auth-brand-panel"
      style={{
        backgroundColor: 'var(--color-surface-dark)',
        flexDirection: 'column',
        padding: 'var(--spacing-xxl)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Decorative shapes */}
      <div
        style={{
          position: 'absolute',
          top: '10%',
          right: '15%',
          width: 280,
          height: 280,
          borderRadius: '50%',
          backgroundColor: 'var(--color-primary)',
          opacity: 0.06,
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '20%',
          left: '10%',
          width: 160,
          height: 160,
          borderRadius: '50%',
          backgroundColor: 'var(--color-accent-teal)',
          opacity: 0.05,
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 500,
          height: 500,
          borderRadius: '50%',
          border: '1px solid rgba(204, 120, 92, 0.08)',
        }}
      />

      {/* Content - centered */}
      <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 420 }}>
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 48,
            fontWeight: 400,
            color: 'var(--color-on-dark)',
            margin: '0 0 var(--spacing-sm)',
            letterSpacing: '-1px',
          }}
        >
          DE hub
        </h2>
        <p style={{ fontSize: 15, color: 'var(--color-on-dark-soft)', margin: '0 0 var(--spacing-xxl)', lineHeight: 1.6 }}>
          开发者的个人空间站
        </p>

        <div
          style={{
            width: 40,
            height: 3,
            backgroundColor: 'var(--color-primary)',
            borderRadius: 'var(--rounded-pill)',
            margin: '0 auto var(--spacing-xl)',
          }}
        />

        <p
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 24,
            fontWeight: 400,
            color: 'var(--color-on-dark)',
            lineHeight: 1.4,
            margin: 0,
            letterSpacing: '-0.3px',
          }}
        >
          {slogan}
        </p>
      </div>
    </div>
  )
}
