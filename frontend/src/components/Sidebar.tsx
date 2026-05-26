import { NavLink, useNavigate } from 'react-router-dom'
import {
  ScrollText,
  Users,
  FileText,
  Settings,
  LayoutDashboard,
  LogOut,
  User,
  Home,
  Database,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { logout } from '../api/users'
import { clearAuth, getUser } from '../utils/auth'

interface NavItem {
  to: string
  label: string
  icon: ReactNode
}

const navItems: NavItem[] = [
  { to: '/admin/logs', label: '日志管理', icon: <ScrollText size={18} /> },
  { to: '/admin/users', label: '用户管理', icon: <Users size={18} /> },
  { to: '/admin/openapi-knowledge', label: '接口知识库', icon: <Database size={18} /> },
  { to: '/admin/content', label: '内容管理', icon: <FileText size={18} /> },
  { to: '/admin/settings', label: '系统设置', icon: <Settings size={18} /> },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const currentUser = getUser()

  const handleLogout = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      await logout(refreshToken ? { refresh_token: refreshToken } : {})
    } catch {
      // ignore
    } finally {
      clearAuth()
      navigate('/login', { replace: true })
    }
  }

  return (
    <aside className="admin-sidebar">
      {/* Logo / Brand */}
      <div
        style={{
          padding: 'var(--spacing-lg) var(--spacing-xl)',
          borderBottom: '1px solid var(--color-surface-dark-elevated)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-sm)',
        }}
      >
        <LayoutDashboard size={22} color="var(--color-primary)" />
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 22,
            fontWeight: 500,
            letterSpacing: '-0.3px',
            color: 'var(--color-on-dark)',
          }}
        >
          管理后台
        </span>
      </div>

      {/* User info */}
      {currentUser && (
        <div
          style={{
            padding: 'var(--spacing-md) var(--spacing-xl)',
            borderBottom: '1px solid var(--color-surface-dark-elevated)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-sm)',
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--rounded-full)',
              backgroundColor: 'var(--color-surface-dark-elevated)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-primary)',
            }}
          >
            <User size={16} />
          </div>
          <div style={{ overflow: 'hidden' }}>
            <div
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: 'var(--color-on-dark)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {currentUser.username}
            </div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--color-on-dark-soft)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {currentUser.email}
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav style={{ padding: 'var(--spacing-md) 0', flex: 1 }}>
        {/* Back to homepage */}
        <NavLink
          to="/"
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-sm)',
            padding: '10px var(--spacing-xl)',
            margin: '4px var(--spacing-md)',
            borderRadius: 'var(--rounded-md)',
            textDecoration: 'none',
            fontSize: 14,
            fontWeight: 500,
            lineHeight: 1.4,
            color: isActive
              ? 'var(--color-on-dark)'
              : 'var(--color-on-dark-soft)',
            backgroundColor: isActive
              ? 'var(--color-surface-dark-elevated)'
              : 'transparent',
            transition: 'all 150ms ease',
          })}
        >
          <span style={{ opacity: 0.9 }}><Home size={18} /></span>
          <span>返回首页</span>
        </NavLink>

        {/* Divider */}
        <div
          style={{
            height: 1,
            backgroundColor: 'var(--color-surface-dark-elevated)',
            margin: 'var(--spacing-sm) var(--spacing-xl) var(--spacing-md)',
          }}
        />

        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              padding: '10px var(--spacing-xl)',
              margin: '4px var(--spacing-md)',
              borderRadius: 'var(--rounded-md)',
              textDecoration: 'none',
              fontSize: 14,
              fontWeight: 500,
              lineHeight: 1.4,
              color: isActive
                ? 'var(--color-on-dark)'
                : 'var(--color-on-dark-soft)',
              backgroundColor: isActive
                ? 'var(--color-surface-dark-elevated)'
                : 'transparent',
              transition: 'all 150ms ease',
            })}
          >
            <span style={{ opacity: 0.9 }}>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div
        style={{
          padding: 'var(--spacing-md) var(--spacing-xl)',
          borderTop: '1px solid var(--color-surface-dark-elevated)',
        }}
      >
        <button
          onClick={handleLogout}
          style={{
            width: '100%',
            height: 36,
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'transparent',
            border: '1px solid var(--color-surface-dark-elevated)',
            color: 'var(--color-on-dark-soft)',
            fontSize: 13,
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 6,
            cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-dark-elevated)'
            e.currentTarget.style.color = 'var(--color-on-dark)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent'
            e.currentTarget.style.color = 'var(--color-on-dark-soft)'
          }}
        >
          <LogOut size={14} />
          登出
        </button>
      </div>
    </aside>
  )
}
