import { X } from 'lucide-react'
import type { ReactNode } from 'react'

interface BaseModalProps {
  title: ReactNode
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
  maxWidth?: number
  borderRadius?: 'lg' | 'xl'
  showCloseButton?: boolean
  closeOnOverlayClick?: boolean
  hideHeaderDivider?: boolean
  hideFooterDivider?: boolean
  overflow?: 'auto' | 'hidden'
  panelPadding?: boolean
}

export default function BaseModal({
  title,
  onClose,
  children,
  footer,
  maxWidth = 520,
  borderRadius = 'lg',
  showCloseButton = true,
  closeOnOverlayClick = true,
  hideHeaderDivider = false,
  hideFooterDivider = false,
  overflow = 'hidden',
  panelPadding = false,
}: BaseModalProps) {
  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        backgroundColor: 'rgba(20,20,19,0.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--spacing-xl)',
      }}
      onClick={(e) => {
        if (closeOnOverlayClick && e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div
        style={{
          backgroundColor: 'var(--color-canvas)',
          borderRadius: borderRadius === 'xl' ? 'var(--rounded-xl)' : 'var(--rounded-lg)',
          width: '100%',
          maxWidth,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow,
          boxShadow: '0 8px 32px rgba(20,20,19,0.15)',
          ...(panelPadding ? { padding: 'var(--spacing-xl)' } : {}),
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            ...(panelPadding
              ? { marginBottom: 'var(--spacing-lg)' }
              : {
                  padding: 'var(--spacing-lg) var(--spacing-xl)',
                  borderBottom: hideHeaderDivider ? undefined : '1px solid var(--color-hairline)',
                }),
          }}
        >
          <div style={{ fontFamily: 'var(--font-display)', color: 'var(--color-ink)', fontWeight: 500, margin: 0 }}>
            {title}
          </div>
          {showCloseButton && (
            <button
              onClick={onClose}
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--rounded-full)',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-muted)',
                flexShrink: 0,
              }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Body */}
        <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: 'var(--spacing-sm)',
              ...(panelPadding
                ? { marginTop: 'var(--spacing-sm)' }
                : {
                    padding: 'var(--spacing-md) var(--spacing-xl)',
                    borderTop: hideFooterDivider ? undefined : '1px solid var(--color-hairline)',
                  }),
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
