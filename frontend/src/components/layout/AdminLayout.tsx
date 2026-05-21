import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  Terminal,
  LayoutDashboard,
  Users,
  Tags,
  FileText,
  Map,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  LogOut,
  ArrowLeft,
} from 'lucide-react'
import { ADMIN_NAV_ITEMS, APP_NAME } from '@/constants'
import { cn } from '@/lib/utils'

const iconMap: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard className="h-4 w-4" />,
  Users: <Users className="h-4 w-4" />,
  Tags: <Tags className="h-4 w-4" />,
  FileText: <FileText className="h-4 w-4" />,
  Map: <Map className="h-4 w-4" />,
  ShieldAlert: <ShieldAlert className="h-4 w-4" />,
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex min-h-svh bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          'sticky top-0 flex h-svh flex-col border-r border-border bg-card transition-all duration-300',
          collapsed ? 'w-16' : 'w-60'
        )}
      >
        {/* Logo */}
        <div className="flex h-14 items-center border-b border-border px-4">
          <Link to="/admin" className="flex items-center gap-2 overflow-hidden">
            <Terminal className="h-5 w-5 shrink-0 text-primary" />
            {!collapsed && <span className="font-bold whitespace-nowrap">{APP_NAME}</span>}
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2">
          <div className="mb-2 px-2">
            {!collapsed && (
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                管理菜单
              </span>
            )}
          </div>
          <div className="flex flex-col gap-1">
            {ADMIN_NAV_ITEMS.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  location.pathname === item.path
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
                title={collapsed ? item.label : undefined}
              >
                {iconMap[item.icon]}
                {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
              </Link>
            ))}
          </div>

          <div className="mt-4 border-t border-border pt-4 px-2">
            <Link
              to="/dashboard"
              className={cn(
                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors',
                collapsed && 'justify-center'
              )}
              title={collapsed ? '返回前台' : undefined}
            >
              <ArrowLeft className="h-4 w-4" />
              {!collapsed && <span>返回前台</span>}
            </Link>
          </div>
        </nav>

        {/* Bottom Actions */}
        <div className="border-t border-border p-2">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex w-full items-center justify-center rounded-md p-2 text-muted-foreground hover:bg-muted transition-colors"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
          <button
            onClick={() => navigate('/login')}
            className={cn(
              'mt-1 flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors',
              collapsed && 'justify-center'
            )}
            title={collapsed ? '退出登录' : undefined}
          >
            <LogOut className="h-4 w-4" />
            {!collapsed && <span>退出登录</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Top Bar */}
        <header className="sticky top-0 z-30 flex h-14 items-center border-b border-border bg-background/80 backdrop-blur-md px-6">
          <h1 className="text-sm font-semibold">
            {ADMIN_NAV_ITEMS.find(item => item.path === location.pathname)?.label || '管理后台'}
          </h1>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
              A
            </div>
            <span className="text-sm text-muted-foreground">Admin</span>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
