import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Settings, LogOut, User, ChevronDown } from 'lucide-react'
import type { User as UserType } from '../../types/user'

interface UserMenuProps {
  user: UserType | null
  onLogout: () => void
  showAdmin?: boolean
}

export default function UserMenu({ user, onLogout, showAdmin = false }: UserMenuProps) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  if (!user) return null

  const menuItems: { label: string; icon: typeof User; onClick: () => void }[] = [
    {
      label: '个人中心',
      icon: User,
      onClick: () => {
        setOpen(false)
        navigate('/profile')
      },
    },
  ]

  if (showAdmin) {
    menuItems.push({
      label: '管理后台',
      icon: Settings,
      onClick: () => {
        setOpen(false)
        navigate('/admin/logs')
      },
    })
  }

  menuItems.push({
    label: '登出',
    icon: LogOut,
    onClick: () => {
      setOpen(false)
      onLogout()
    },
  })

  return (
    <div ref={containerRef} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '4px 10px 4px 4px',
          borderRadius: 'var(--rounded-pill)',
          backgroundColor: open ? 'var(--color-surface-card)' : 'transparent',
          border: '1px solid transparent',
          borderColor: open ? 'var(--color-hairline)' : 'transparent',
          cursor: 'pointer',
          transition: 'background-color 0.2s ease, border-color 0.2s ease',
        }}
        onMouseEnter={(e) => {
          if (!open) e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
        }}
        onMouseLeave={(e) => {
          if (!open) e.currentTarget.style.backgroundColor = 'transparent'
        }}
      >
        {/* Avatar */}
        <div
          style={{
            width: 30,
            height: 30,
            borderRadius: '50%',
            backgroundColor: 'var(--color-surface-card)',
            border: '1px solid var(--color-hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-primary)',
            overflow: 'hidden',
            flexShrink: 0,
          }}
        >
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.username}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <User size={14} />
          )}
        </div>

        <span
          style={{
            fontSize: 13,
            fontWeight: 600,
            color: 'var(--color-body-strong)',
            maxWidth: 120,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {user.username}
        </span>

        <ChevronDown
          size={14}
          color="var(--color-muted-soft)"
          style={{
            transition: 'transform 0.2s ease',
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          }}
        />
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="animate-scaleIn"
          style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            right: 0,
            minWidth: 180,
            backgroundColor: 'var(--color-canvas)',
            borderRadius: 'var(--rounded-lg)',
            border: '1px solid var(--color-hairline)',
            boxShadow: '0 16px 40px rgba(20, 20, 19, 0.12)',
            padding: 'var(--spacing-xs)',
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            zIndex: 100,
            transformOrigin: 'top right',
          }}
        >
          {menuItems.map((item, idx) => {
            const isLast = idx === menuItems.length - 1
            return (
              <button
                key={item.label}
                onClick={item.onClick}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--spacing-sm)',
                  padding: '10px 12px',
                  borderRadius: 'var(--rounded-md)',
                  backgroundColor: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: 14,
                  fontWeight: 500,
                  color: isLast ? 'var(--color-error)' : 'var(--color-body)',
                  textAlign: 'left',
                  transition: 'background-color 0.15s ease, color 0.15s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = isLast
                    ? 'rgba(198, 69, 69, 0.06)'
                    : 'var(--color-surface-soft)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent'
                }}
              >
                <item.icon size={15} />
                {item.label}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
