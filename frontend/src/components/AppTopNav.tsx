import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Menu, Sparkles, X } from 'lucide-react'
import type { User as UserType } from '../types/user'
import { getUser } from '../utils/auth'
import UserMenu from './ui/UserMenu'

interface AppTopNavProps {
  onLogout: () => void
  forumHref?: string
}

interface NavLinkItem {
  label: string
  href: string
}

const defaultLinks: NavLinkItem[] = [
  { label: '博客', href: '/blogs' },
  { label: '论坛', href: '/forums' },
  { label: 'AI 助手', href: '/ai-chat' },
  { label: '作品集', href: '/portfolio' },
]

function canEnterAdmin(user: UserType | null): boolean {
  return !!user && user.permission >= 1
}

function isActiveLink(pathname: string, href: string): boolean {
  if (href === '/') return pathname === '/'
  if (href === '/forums') return pathname.startsWith('/forums')
  return pathname.startsWith(href)
}

export default function AppTopNav({ onLogout, forumHref = '/forums' }: AppTopNavProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const currentUser = getUser()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const navLinks = defaultLinks.map((link) =>
    link.label === '论坛' ? { ...link, href: forumHref } : link,
  )
  const showAdmin = canEnterAdmin(currentUser)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 8)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    setDrawerOpen(false)
  }, [location.pathname])

  const goTo = (href: string) => {
    setDrawerOpen(false)
    if (href.startsWith('/#')) {
      navigate('/')
      setTimeout(() => {
        const el = document.getElementById(href.slice(2))
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }, 100)
      return
    }
    navigate(href)
  }

  return (
    <>
      <header
        className="app-top-nav"
        style={{
          boxShadow: scrolled
            ? '0 1px 3px rgba(20, 20, 19, 0.06)'
            : 'none',
          transition: 'box-shadow 0.3s ease',
        }}
      >
        {/* Brand */}
        <button
          className="app-top-nav__brand"
          onClick={() => goTo('/')}
          type="button"
          style={{ cursor: 'pointer' }}
        >
          <span
            className="brand-sparkles"
            style={{
              display: 'inline-flex',
              transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'rotate(180deg) scale(1.1)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'rotate(0deg) scale(1)'
            }}
          >
            <Sparkles size={20} />
          </span>
          <span>DE hub</span>
        </button>

        {/* Desktop Nav */}
        <nav className="app-top-nav__links" aria-label="主导航">
          {navLinks.map((link) => {
            const active = isActiveLink(location.pathname, link.href)
            return (
              <button
                key={link.label}
                type="button"
                onClick={() => goTo(link.href)}
                className="nav-link-underline"
                style={{
                  position: 'relative',
                  fontSize: 14,
                  fontWeight: 600,
                  color: active ? 'var(--color-ink)' : 'var(--color-body)',
                  paddingBottom: 4,
                  transition: 'color 0.2s ease',
                }}
              >
                {link.label}
                {active && (
                  <span
                    style={{
                      position: 'absolute',
                      left: 0,
                      bottom: -2,
                      width: '100%',
                      height: 2,
                      backgroundColor: 'var(--color-primary)',
                      borderRadius: 'var(--rounded-pill)',
                      animation: 'nav-underline-in 0.3s ease forwards',
                    }}
                  />
                )}
              </button>
            )
          })}
        </nav>

        {/* Actions */}
        <div className="app-top-nav__actions">
          <div className="app-top-nav__desktop-actions">
            {currentUser && (
              <UserMenu user={currentUser} onLogout={onLogout} showAdmin={showAdmin} />
            )}
          </div>

          <button
            className="app-top-nav__menu"
            onClick={() => setDrawerOpen((v) => !v)}
            type="button"
            aria-label={drawerOpen ? '关闭导航菜单' : '打开导航菜单'}
            aria-expanded={drawerOpen}
          >
            {drawerOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {drawerOpen && (
        <>
          <div
            className="drawer-overlay"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="drawer-panel">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 'var(--spacing-lg)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--spacing-sm)',
                  color: 'var(--color-primary)',
                }}
              >
                <Sparkles size={18} />
                <span
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: 18,
                    fontWeight: 500,
                    color: 'var(--color-ink)',
                  }}
                >
                  DE hub
                </span>
              </div>
              <button
                onClick={() => setDrawerOpen(false)}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 'var(--rounded-md)',
                  border: '1px solid var(--color-hairline)',
                  backgroundColor: 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-muted)',
                  cursor: 'pointer',
                }}
              >
                <X size={16} />
              </button>
            </div>

            <nav style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1 }}>
              {navLinks.map((link) => {
                const active = isActiveLink(location.pathname, link.href)
                return (
                  <button
                    key={link.label}
                    type="button"
                    onClick={() => goTo(link.href)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--spacing-sm)',
                      padding: '12px 14px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: active ? 'var(--color-surface-card)' : 'transparent',
                      color: active ? 'var(--color-ink)' : 'var(--color-body)',
                      fontSize: 15,
                      fontWeight: 500,
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      if (!active) e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                    }}
                    onMouseLeave={(e) => {
                      if (!active) e.currentTarget.style.backgroundColor = 'transparent'
                    }}
                  >
                    {link.label}
                    {active && (
                      <span
                        style={{
                          marginLeft: 'auto',
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          backgroundColor: 'var(--color-primary)',
                        }}
                      />
                    )}
                  </button>
                )
              })}

              <div
                style={{
                  height: 1,
                  backgroundColor: 'var(--color-hairline-soft)',
                  margin: 'var(--spacing-sm) 0',
                }}
              />

              {currentUser && (
                <>
                  <button
                    type="button"
                    onClick={() => goTo('/profile')}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--spacing-sm)',
                      padding: '12px 14px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: 'transparent',
                      color: 'var(--color-body)',
                      fontSize: 15,
                      fontWeight: 500,
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent'
                    }}
                  >
                    {currentUser.username}
                  </button>
                  {showAdmin && (
                    <button
                      type="button"
                      onClick={() => goTo('/admin/logs')}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--spacing-sm)',
                        padding: '12px 14px',
                        borderRadius: 'var(--rounded-md)',
                        backgroundColor: 'transparent',
                        color: 'var(--color-body)',
                        fontSize: 15,
                        fontWeight: 500,
                        border: 'none',
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'background-color 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'var(--color-surface-soft)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent'
                      }}
                    >
                      管理后台
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={onLogout}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--spacing-sm)',
                      padding: '12px 14px',
                      borderRadius: 'var(--rounded-md)',
                      backgroundColor: 'transparent',
                      color: 'var(--color-error)',
                      fontSize: 15,
                      fontWeight: 500,
                      border: 'none',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'background-color 0.15s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(198, 69, 69, 0.06)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'transparent'
                    }}
                  >
                    登出
                  </button>
                </>
              )}
            </nav>
          </div>
        </>
      )}
    </>
  )
}
