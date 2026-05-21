import { Link } from 'react-router-dom'
import { BookOpen, MessageSquare, Bot, ArrowRight, TrendingUp, Clock } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

const quickLinks = [
  { title: '博客', desc: '阅读技术文章与教程', icon: BookOpen, path: '/blog', color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  { title: '论坛', desc: '参与讨论与交流', icon: MessageSquare, path: '/forum', color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { title: 'AI对话', desc: '智能助手答疑解惑', icon: Bot, path: '/ai-chat', color: 'text-violet-500', bg: 'bg-violet-500/10' },
]

const recentPosts = [
  { title: 'React 19 新特性详解', category: '前端开发', views: 1205, time: '2小时前' },
  { title: 'FastAPI 性能优化指南', category: '后端开发', views: 892, time: '5小时前' },
  { title: 'LangGraph 工作流设计模式', category: 'AI', views: 1567, time: '1天前' },
  { title: 'PostgreSQL 向量搜索实战', category: '数据库', views: 743, time: '2天前' },
]

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Welcome */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold">欢迎回来，Developer</h1>
        <p className="mt-1 text-muted-foreground">这里是你的开发者个人空间</p>
      </div>

      {/* Quick Links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 mb-8">
        {quickLinks.map(link => (
          <Link key={link.path} to={link.path}>
            <Card className="h-full transition-all hover:border-primary/50 hover:shadow-md group">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className={`rounded-lg ${link.bg} p-3`}>
                    <link.icon className={`h-5 w-5 ${link.color}`} />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
                </div>
                <h3 className="mt-4 font-semibold">{link.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{link.desc}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Posts */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>最近更新</CardTitle>
              <Link to="/blog" className="text-sm text-primary hover:underline">查看全部</Link>
            </div>
            <CardDescription>最新的博客文章与论坛动态</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentPosts.map((post, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg border border-border p-4 transition-colors hover:bg-muted/50">
                  <div>
                    <h4 className="font-medium">{post.title}</h4>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">{post.category}</Badge>
                      <span className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3" />
                        {post.views} 浏览
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {post.time}
                      </span>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm">阅读</Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Stats */}
        <Card>
          <CardHeader>
            <CardTitle>数据概览</CardTitle>
            <CardDescription>你的个人统计</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <span className="text-sm text-muted-foreground">发表文章</span>
                <span className="text-lg font-bold">0</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <span className="text-sm text-muted-foreground">论坛帖子</span>
                <span className="text-lg font-bold">0</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <span className="text-sm text-muted-foreground">获赞总数</span>
                <span className="text-lg font-bold">0</span>
              </div>
              <div className="flex items-center justify-between rounded-lg border border-border p-4">
                <span className="text-sm text-muted-foreground">收藏文章</span>
                <span className="text-lg font-bold">0</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
