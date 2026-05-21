import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Terminal,
  Sun,
  Moon,
  Menu,
  X,
  User,
  LogOut,
  Settings,
  Heart,
  MapPin,
  ChevronDown,
  Shield,
} from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { NAV_ITEMS, USER_MENU_ITEMS, APP_NAME } from '@/constants'
import { cn } from '@/lib/utils'

export default function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  // Mock auth state - replace with real auth later
  const isAuthenticated = true
  const user = {
    username: 'Developer',
    avatar_url: null,
    permission: 2,
  }

  const isAdmin = user.permission >= 1

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link to="/dashboard" className="flex items-center gap-2">
          <Terminal className="h-5 w-5 text-primary" />
          <span className="text-lg font-bold tracking-tight">{APP_NAME}</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden items-center gap-1 md:flex">
          {isAuthenticated && NAV_ITEMS.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                location.pathname === item.path || location.pathname.startsWith(item.path + '/')
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="切换主题"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          {/* User Menu */}
          {isAuthenticated ? (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 rounded-md p-1.5 pr-3 text-sm hover:bg-muted transition-colors"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline">{user.username}</span>
                <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
              </button>

              {userMenuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setUserMenuOpen(false)} />
                  <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-border bg-card p-1 shadow-lg z-20 animate-fade-in">
                    {USER_MENU_ITEMS.map(item => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-foreground hover:bg-muted transition-colors"
                      >
                        {item.label === '个人资料' && <User className="h-4 w-4" />}
                        {item.label === '我的收藏' && <Heart className="h-4 w-4" />}
                        {item.label === '我的关注' && <MapPin className="h-4 w-4" />}
                        {item.label === '设置' && <Settings className="h-4 w-4" />}
                        {item.label}
                      </Link>
                    ))}
                    {isAdmin && (
                      <Link
                        to="/admin"
                        onClick={() => setUserMenuOpen(false)}
                        className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-primary hover:bg-primary/10 transition-colors"
                      >
                        <Shield className="h-4 w-4" />
                        管理后台
                      </Link>
                    )}
                    <div className="my-1 border-t border-border" />
                    <button
                      onClick={() => {
                        setUserMenuOpen(false)
                        navigate('/login')
                      }}
                      className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-destructive hover:bg-destructive/10 transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      退出登录
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="hidden items-center gap-2 md:flex">
              <Link
                to="/login"
                className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                登录
              </Link>
              <Link
                to="/register"
                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                注册
              </Link>
            </div>
          )}

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="rounded-md p-2 text-muted-foreground hover:bg-muted md:hidden"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="border-t border-border bg-background px-4 py-3 md:hidden animate-fade-in">
          <nav className="flex flex-col gap-1">
            {isAuthenticated && NAV_ITEMS.map(item => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  'rounded-md px-3 py-2 text-sm font-medium',
                  location.pathname === item.path
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-muted'
                )}
              >
                {item.label}
              </Link>
            ))}
            {!isAuthenticated && (
              <>
                <Link to="/login" onClick={() => setMobileOpen(false)} className="rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted">
                  登录
                </Link>
                <Link to="/register" onClick={() => setMobileOpen(false)} className="rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground text-center">
                  注册
                </Link>
              </>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
