export const APP_NAME = 'DEhub'
export const APP_DESCRIPTION = '开发者个人网站'

export const NAV_ITEMS = [
  { label: '仪表盘', path: '/dashboard' },
  { label: '博客', path: '/blog' },
  { label: '论坛', path: '/forum' },
  { label: 'AI对话', path: '/ai-chat' },
]

export const ADMIN_NAV_ITEMS = [
  { label: '仪表盘', path: '/admin', icon: 'LayoutDashboard' },
  { label: '用户管理', path: '/admin/users', icon: 'Users' },
  { label: '博客分类', path: '/admin/blog-categories', icon: 'Tags' },
  { label: '博客文章', path: '/admin/blog-posts', icon: 'FileText' },
  { label: '论坛分区', path: '/admin/forum-zones', icon: 'Map' },
  { label: '系统日志', path: '/admin/system-logs', icon: 'ShieldAlert' },
]

export const USER_MENU_ITEMS = [
  { label: '个人资料', path: '/profile' },
  { label: '我的收藏', path: '/favorites' },
  { label: '我的关注', path: '/follows' },
  { label: '设置', path: '/settings' },
]

export const PERMISSION_LABELS: Record<number, string> = {
  0: '普通用户',
  1: '管理员',
  2: '超级管理员',
}

export const LOG_LEVEL_COLORS: Record<string, string> = {
  WARN: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
  ERROR: 'bg-orange-500/10 text-orange-600 border-orange-500/20',
  CRITICAL: 'bg-red-500/10 text-red-600 border-red-500/20',
}

export const LOG_LEVEL_BADGE_COLORS: Record<string, string> = {
  WARN: 'bg-yellow-500 text-white',
  ERROR: 'bg-orange-500 text-white',
  CRITICAL: 'bg-red-500 text-white',
}

export const DEFAULT_AVATAR = 'https://api.dicebear.com/7.x/avataaars/svg?seed='
