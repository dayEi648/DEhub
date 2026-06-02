import React, { useRef, useCallback } from 'react'

interface RippleButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'ghost' | 'dark'
  size?: 'sm' | 'md' | 'lg'
  fullWidth?: boolean
}

export default function RippleButton({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  style,
  onClick,
  ...props
}: RippleButtonProps) {
  const btnRef = useRef<HTMLButtonElement>(null)

  const handleClick = useCallback(
    (e: React.MouseEvent<HTMLButtonElement>) => {
      const btn = btnRef.current
      if (!btn) return

      const rect = btn.getBoundingClientRect()
      const size = Math.max(rect.width, rect.height)
      const x = e.clientX - rect.left - size / 2
      const y = e.clientY - rect.top - size / 2

      const ripple = document.createElement('span')
      ripple.className = 'ripple-span'
      ripple.style.width = ripple.style.height = `${size}px`
      ripple.style.left = `${x}px`
      ripple.style.top = `${y}px`

      btn.appendChild(ripple)
      setTimeout(() => ripple.remove(), 600)

      onClick?.(e)
    },
    [onClick]
  )

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: 'var(--color-primary)',
      color: 'var(--color-on-primary)',
      border: '1px solid transparent',
    },
    secondary: {
      backgroundColor: 'var(--color-canvas)',
      color: 'var(--color-ink)',
      border: '1px solid var(--color-hairline)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--color-muted)',
      border: '1px solid var(--color-hairline)',
    },
    dark: {
      backgroundColor: 'var(--color-surface-dark-elevated)',
      color: 'var(--color-on-dark)',
      border: '1px solid transparent',
    },
  }

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { height: 32, padding: '0 12px', fontSize: 13 },
    md: { height: 40, padding: '0 20px', fontSize: 14 },
    lg: { height: 44, padding: '0 24px', fontSize: 14 },
  }

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderRadius: 'var(--rounded-md)',
    fontWeight: 500,
    cursor: props.disabled ? 'not-allowed' : 'pointer',
    opacity: props.disabled ? 0.55 : 1,
    width: fullWidth ? '100%' : undefined,
    transition: 'background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease',
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...style,
  }

  const handleMouseEnter = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (props.disabled) return
    const target = e.currentTarget
    if (variant === 'primary') {
      target.style.backgroundColor = 'var(--color-primary-active)'
    } else if (variant === 'secondary') {
      target.style.backgroundColor = 'var(--color-surface-soft)'
    } else if (variant === 'ghost') {
      target.style.backgroundColor = 'var(--color-surface-soft)'
      target.style.color = 'var(--color-ink)'
    } else if (variant === 'dark') {
      target.style.backgroundColor = 'var(--color-surface-dark-soft)'
    }
    target.style.transform = 'translateY(-1px)'
  }

  const handleMouseLeave = (e: React.MouseEvent<HTMLButtonElement>) => {
    const target = e.currentTarget
    target.style.backgroundColor = variantStyles[variant].backgroundColor as string
    target.style.color = variantStyles[variant].color as string
    target.style.transform = 'translateY(0)'
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!props.disabled) {
      e.currentTarget.style.transform = 'scale(0.97)'
    }
  }

  const handleMouseUp = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.currentTarget.style.transform = 'scale(1)'
  }

  return (
    <button
      ref={btnRef}
      {...props}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      className={`ripple-container ${variant === 'dark' ? 'ripple-container--dark' : ''} ${props.className || ''}`}
      style={baseStyle}
    >
      {children}
    </button>
  )
}
