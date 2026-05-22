import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LayoutGrid,
  Sparkles,
  LogOut,
  User,
  Settings,
  Eye,
  MessageSquare,
} from 'lucide-react'
import { getForumZoneList } from '../api/forum'
import { logout } from '../api/users'
import { clearAuth, getUser } from '../utils/auth'
import type { ForumZone } from '../types/forum'

/* ─── Helpers ─── */
/* ─── TopNav ─── */
function TopNav({ onLogout }: { onLogout: () => void }) {
  const currentUser = getUser()
  const navigate = useNavigate()

  const navLinks = [
    { label: '博客', href: '/blogs' },
    { label: '论坛', href: '/forums' },
    { label: '作品集', href: '/#portfolio' },
  ]

  const linkStyle: React.CSSProperties = {
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--color-ink)',
    textDecoration: 'none',
    lineHeight: 1.4,
    transition: 'color 150ms ease',
  }

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        height: 64,
        backgroundColor: 'var(--color-canvas)',
        borderBottom: '1px solid var(--color-hairline-soft)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 var(--spacing-xl)',
      }}
    >
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', cursor: 'pointer' }}
        onClick={() => navigate('/')}
      >
        <Sparkles size={20} color="var(--color-primary)" />
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 20,
            fontWeight: 500,
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
          }}
        >
          DE hub
        </span>
      </div>

      <nav style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-lg)' }}>
        {navLinks.map((l) => (
          <a
            key={l.label}
            href={l.href}
            style={linkStyle}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--color-primary)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--color-ink)'
            }}
          >
            {l.label}
          </a>
        ))}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)' }}>
        <button
          onClick={() => navigate('/admin/logs')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 13,
            fontWeight: 500,
            color: 'var(--color-muted)',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            transition: 'color 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--color-ink)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--color-muted)'
          }}
        >
          <Settings size={15} />
          管理后台
        </button>

        {currentUser && (
          <button
            onClick={() => navigate('/profile')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--spacing-sm)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: 'var(--rounded-md)',
              transition: 'background-color 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 'var(--rounded-full)',
                backgroundColor: 'var(--color-surface-card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-primary)',
              }}
            >
              <User size={14} />
            </div>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-body-strong)' }}>
              {currentUser.username}
            </span>
          </button>
        )}

        <button
          onClick={onLogout}
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--rounded-full)',
            backgroundColor: 'var(--color-canvas)',
            border: '1px solid var(--color-hairline)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-ink)',
            cursor: 'pointer',
            transition: 'all 150ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-surface-card)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--color-canvas)'
          }}
          title="登出"
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  )
}

/* ─── Hero ─── */
function HeroSection() {
  return (
    <section
      style={{
        backgroundColor: 'var(--color-canvas)',
        padding: 'var(--spacing-section) var(--spacing-xl)',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            padding: '4px 12px',
            borderRadius: 'var(--rounded-pill)',
            backgroundColor: 'var(--color-surface-card)',
            fontSize: 12,
            fontWeight: 500,
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            color: 'var(--color-primary)',
            marginBottom: 'var(--spacing-md)',
          }}
        >
          <MessageSquare size={12} />
          论坛
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(36px, 5vw, 64px)',
            fontWeight: 400,
            lineHeight: 1.05,
            letterSpacing: '-1.5px',
            color: 'var(--color-ink)',
            margin: '0 0 var(--spacing-sm)',
          }}
        >
          社区分区
        </h1>
        <p
          style={{
            fontSize: 18,
            lineHeight: 1.55,
            color: 'var(--color-muted)',
            margin: 0,
            maxWidth: 560,
          }}
        >
          选择你感兴趣的分区，参与讨论、分享经验、与开发者共同成长。
        </p>
      </div>
    </section>
  )
}

/* ─── Zone Card ─── */
function ZoneCard({ zone }: { zone: ForumZone }) {
  const navigate = useNavigate()

  return (
    <article
      onClick={() => navigate(`/forums/z/${zone.slug}`)}
      style={{
        backgroundColor: 'var(--color-surface-card)',
        borderRadius: 'var(--rounded-lg)',
        padding: 'var(--spacing-xl)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--spacing-sm)',
        cursor: 'pointer',
        transition: 'transform 150ms ease, box-shadow 150ms ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(20,20,19,0.06)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', marginBottom: 2 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--rounded-md)',
            backgroundColor: 'var(--color-canvas)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--color-primary)',
          }}
        >
          <LayoutGrid size={18} />
        </div>
        <h3
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 22,
            fontWeight: 400,
            lineHeight: 1.2,
            letterSpacing: '-0.3px',
            color: 'var(--color-ink)',
            margin: 0,
            flex: 1,
          }}
        >
          {zone.zone_name}
        </h3>
      </div>

      <p
        style={{
          fontSize: 14,
          lineHeight: 1.55,
          color: 'var(--color-muted)',
          margin: 0,
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical' as const,
          overflow: 'hidden',
          minHeight: 44,
        }}
      >
        {zone.description || '暂无描述'}
      </p>

      <div
        style={{
          marginTop: 'auto',
          paddingTop: 'var(--spacing-sm)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: 13,
          color: 'var(--color-muted-soft)',
        }}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Eye size={12} />
          {zone.view_count} 浏览
        </span>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <User size={12} />
          {zone.manager.username}
        </span>
      </div>
    </article>
  )
}

/* ─── Footer ─── */
function Footer() {
  return (
    <footer
      style={{
        backgroundColor: 'var(--color-surface-dark)',
        color: 'var(--color-on-dark-soft)',
        padding: 'var(--spacing-xl) var(--spacing-xl)',
        marginTop: 'auto',
      }}
    >
      <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-md)' }}>
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

/* ─── Main Page ─── */
export default function ForumZoneListPage() {
  const navigate = useNavigate()
  const [zones, setZones] = useState<ForumZone[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchZones = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getForumZoneList()
      setZones(res.data)
    } catch {
      setError('加载分区失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchZones()
  }, [fetchZones])

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
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-canvas)' }}>
      <TopNav onLogout={handleLogout} />
      <HeroSection />

      <section style={{ flex: 1, padding: 'var(--spacing-xl) var(--spacing-xl)', backgroundColor: 'var(--color-canvas)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              加载中...
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-error)' }}>
              {error}
            </div>
          ) : zones.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 'var(--spacing-section) 0', color: 'var(--color-muted)' }}>
              <LayoutGrid size={48} style={{ marginBottom: 'var(--spacing-md)', opacity: 0.3 }} />
              <p style={{ fontSize: 16, margin: 0 }}>暂无分区</p>
            </div>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: 'var(--spacing-lg)',
              }}
            >
              {zones.map((zone) => (
                <ZoneCard key={zone.id} zone={zone} />
              ))}
            </div>
          )}
        </div>
      </section>

      <Footer />
    </div>
  )
}
