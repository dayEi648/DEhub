import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Menu, Settings, Sparkles, User, X } from 'lucide-react'
import type { User as UserType } from '../types/user'
import { getUser } from '../utils/auth'

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
  { label: '作品集', href: '/#portfolio' },
]

function canEnterAdmin(user: UserType | null): boolean {
  return !!user && user.permission >= 1
}

export default function AppTopNav({ onLogout, forumHref = '/forums' }: AppTopNavProps) {
  const navigate = useNavigate()
  const currentUser = getUser()
  const [open, setOpen] = useState(false)
  const navLinks = defaultLinks.map((link) =>
    link.label === '论坛' ? { ...link, href: forumHref } : link,
  )
  const showAdmin = canEnterAdmin(currentUser)

  const goTo = (href: string) => {
    setOpen(false)
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
    <header className="app-top-nav">
      <button className="app-top-nav__brand" onClick={() => goTo('/')} type="button">
        <Sparkles size={20} />
        <span>DE hub</span>
      </button>

      <nav className="app-top-nav__links" aria-label="主导航">
        {navLinks.map((link) => (
          <button key={link.label} type="button" onClick={() => goTo(link.href)}>
            {link.label}
          </button>
        ))}
      </nav>

      <div className="app-top-nav__actions">
        {showAdmin && (
          <button className="app-top-nav__admin" onClick={() => goTo('/admin/logs')} type="button">
            <Settings size={15} />
            <span>管理后台</span>
          </button>
        )}

        {currentUser && (
          <button className="app-top-nav__profile" onClick={() => goTo('/profile')} type="button">
            <span className="app-top-nav__avatar">
              <User size={14} />
            </span>
            <span className="app-top-nav__username">{currentUser.username}</span>
          </button>
        )}

        <button className="app-top-nav__logout" onClick={onLogout} type="button" title="登出">
          <LogOut size={15} />
        </button>

        <button
          className="app-top-nav__menu"
          onClick={() => setOpen((value) => !value)}
          type="button"
          aria-label={open ? '关闭导航菜单' : '打开导航菜单'}
          aria-expanded={open}
        >
          {open ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {open && (
        <div className="app-top-nav__drawer">
          {navLinks.map((link) => (
            <button key={link.label} type="button" onClick={() => goTo(link.href)}>
              {link.label}
            </button>
          ))}
          {showAdmin && (
            <button type="button" onClick={() => goTo('/admin/logs')}>
              管理后台
            </button>
          )}
          <button type="button" onClick={() => goTo('/profile')}>
            个人中心
          </button>
          <button type="button" onClick={onLogout}>
            登出
          </button>
        </div>
      )}
    </header>
  )
}
