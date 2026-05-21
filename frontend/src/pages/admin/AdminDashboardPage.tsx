import { Users, FileText, MessageSquare, ShieldAlert, TrendingUp } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'

const stats = [
  { title: '用户总数', value: 128, icon: Users, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { title: '博客文章', value: 45, icon: FileText, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  { title: '论坛帖子', value: 892, icon: MessageSquare, color: 'text-violet-500', bg: 'bg-violet-500/10' },
  { title: '未处理日志', value: 5, icon: ShieldAlert, color: 'text-red-500', bg: 'bg-red-500/10' },
]

const recentActivity = [
  { action: '新用户注册', detail: '用户 CodeMaster 注册了账户', time: '5分钟前' },
  { action: '文章发布', detail: '超级管理员发布了《React 19 新特性详解》', time: '30分钟前' },
  { action: '错误日志', detail: '数据库连接超时 WARN', time: '1小时前' },
  { action: '帖子删除', detail: '管理员删除了违规帖子', time: '2小时前' },
]

export default function AdminDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">管理仪表盘</h1>
        <p className="text-sm text-muted-foreground">系统概览与快捷操作</p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(stat => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`rounded-lg ${stat.bg} p-3`}>
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions & Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>快捷操作</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <a href="/admin/users" className="rounded-lg border border-border p-4 text-center hover:bg-muted transition-colors">
                <Users className="h-5 w-5 mx-auto mb-2 text-primary" />
                <span className="text-sm font-medium">用户管理</span>
              </a>
              <a href="/admin/blog-posts" className="rounded-lg border border-border p-4 text-center hover:bg-muted transition-colors">
                <FileText className="h-5 w-5 mx-auto mb-2 text-primary" />
                <span className="text-sm font-medium">文章管理</span>
              </a>
              <a href="/admin/forum-zones" className="rounded-lg border border-border p-4 text-center hover:bg-muted transition-colors">
                <MessageSquare className="h-5 w-5 mx-auto mb-2 text-primary" />
                <span className="text-sm font-medium">论坛分区</span>
              </a>
              <a href="/admin/system-logs" className="rounded-lg border border-border p-4 text-center hover:bg-muted transition-colors">
                <ShieldAlert className="h-5 w-5 mx-auto mb-2 text-primary" />
                <span className="text-sm font-medium">系统日志</span>
              </a>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>最近活动</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentActivity.map((item, i) => (
                <div key={i} className="flex items-start gap-3 rounded-lg border border-border p-3">
                  <TrendingUp className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-medium">{item.action}</p>
                    <p className="text-xs text-muted-foreground">{item.detail}</p>
                    <p className="text-xs text-muted-foreground mt-1">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
