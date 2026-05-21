import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Plus, TrendingUp, Clock, MessageSquare, Eye } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Pagination from '@/components/ui/Pagination'
import Avatar from '@/components/ui/Avatar'
import { cn } from '@/lib/utils'

const MOCK_POSTS = [
  {
    id: 1,
    title: 'React 19 的 use() Hook 有什么实际使用场景？',
    content: '看了文档 but 还是不太理解在什么情况下应该用 use() 而不是 useEffect...',
    user: { username: 'CuriousDev', avatar_url: null },
    view_count: 234,
    reply_count: 18,
    created_at: '2024-01-15T10:00:00',
  },
  {
    id: 2,
    title: '求推荐好用的 React 状态管理库',
    content: '项目越来越大，useState 和 Context 已经不够用了，Zustand 和 Jotai 哪个更好？',
    user: { username: 'StateConfused', avatar_url: null },
    view_count: 567,
    reply_count: 42,
    created_at: '2024-01-14T15:30:00',
  },
  {
    id: 3,
    title: 'Tailwind CSS v4 配置方式变化大吗？',
    content: '看到 v4 用 CSS 导入的方式配置了，和 v3 的 tailwind.config.js 相比有什么优劣？',
    user: { username: 'CSSWizard', avatar_url: null },
    view_count: 189,
    reply_count: 12,
    created_at: '2024-01-13T09:00:00',
  },
  {
    id: 4,
    title: '分享一个自己写的 Vite 插件',
    content: '可以自动分析路由并生成 sitemap，已经用在生产环境了...',
    user: { username: 'PluginAuthor', avatar_url: null },
    view_count: 445,
    reply_count: 28,
    created_at: '2024-01-12T11:00:00',
  },
]

export default function ZonePostsPage() {
  useParams()
  const [sortBy, setSortBy] = useState<'created' | 'view'>('created')
  const [currentPage, setCurrentPage] = useState(1)

  const zone = { zone_name: '前端开发', description: 'HTML, CSS, JavaScript, React, Vue 等前端技术讨论区' }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Back & Header */}
      <Link to="/forum" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4">
        <ArrowLeft className="h-4 w-4" />
        返回论坛首页
      </Link>

      <div className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">{zone.zone_name}</h1>
          <p className="mt-1 text-muted-foreground">{zone.description}</p>
        </div>
        <Button className="gap-1">
          <Plus className="h-4 w-4" />
          发表新帖
        </Button>
      </div>

      {/* Sort */}
      <div className="mb-4 flex items-center gap-2">
        <span className="text-sm text-muted-foreground">排序：</span>
        <button
          onClick={() => setSortBy('created')}
          className={cn(
            'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
            sortBy === 'created' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'
          )}
        >
          <Clock className="h-3.5 w-3.5" />
          最新
        </button>
        <button
          onClick={() => setSortBy('view')}
          className={cn(
            'flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
            sortBy === 'view' ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted'
          )}
        >
          <TrendingUp className="h-3.5 w-3.5" />
          最热
        </button>
      </div>

      {/* Posts List */}
      <div className="space-y-3">
        {MOCK_POSTS.map(post => (
          <Link key={post.id} to={`/forum/post/${post.id}`}>
            <Card className="transition-all hover:border-primary/50">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <Avatar name={post.user.username} size="md" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground hover:text-primary transition-colors">
                      {post.title}
                    </h3>
                    <p className="mt-1 text-sm text-muted-foreground line-clamp-1">{post.content}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-muted-foreground">
                      <span>{post.user.username}</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(post.created_at).toLocaleDateString('zh-CN')}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-3 w-3" />
                        {post.view_count}
                      </span>
                      <span className="flex items-center gap-1">
                        <MessageSquare className="h-3 w-3" />
                        {post.reply_count}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pagination */}
      <div className="mt-8 flex justify-center">
        <Pagination currentPage={currentPage} totalPages={8} onPageChange={setCurrentPage} />
      </div>
    </div>
  )
}
