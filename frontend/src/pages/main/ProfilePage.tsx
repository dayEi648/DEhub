import { Calendar, Mail, Edit } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Avatar from '@/components/ui/Avatar'
import { formatDateTime } from '@/lib/utils'

// Mock user data - 注意不显示 id、password、permission、is_deleted 等敏感字段
const MOCK_USER = {
  username: 'Developer',
  email: 'dev@example.com',
  avatar_url: null,
  personal_profile: '热爱技术，专注于全栈开发和人工智能应用。喜欢探索新技术，分享学习心得。',
  created_at: '2024-01-01T00:00:00',
}

const MOCK_STATS = {
  posts: 12,
  forum_posts: 28,
  comments: 156,
  likes_received: 342,
}

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Profile Header */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
            <Avatar name={MOCK_USER.username} size="lg" className="h-20 w-20 text-2xl" />
            <div className="flex-1 text-center sm:text-left">
              <h1 className="text-2xl font-bold">{MOCK_USER.username}</h1>
              <p className="mt-1 text-muted-foreground">{MOCK_USER.personal_profile}</p>
              <div className="mt-3 flex flex-wrap items-center justify-center gap-3 text-sm text-muted-foreground sm:justify-start">
                <span className="flex items-center gap-1">
                  <Mail className="h-4 w-4" />
                  {MOCK_USER.email}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  注册于 {formatDateTime(MOCK_USER.created_at)}
                </span>
              </div>
            </div>
            <Button variant="outline" size="sm" className="gap-1">
              <Edit className="h-4 w-4" />
              编辑资料
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4 mb-6">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{MOCK_STATS.posts}</div>
            <div className="text-xs text-muted-foreground">博客文章</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{MOCK_STATS.forum_posts}</div>
            <div className="text-xs text-muted-foreground">论坛帖子</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{MOCK_STATS.comments}</div>
            <div className="text-xs text-muted-foreground">评论</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{MOCK_STATS.likes_received}</div>
            <div className="text-xs text-muted-foreground">获赞</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>最近动态</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 rounded-lg border border-border p-3">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm">评论了文章《React 19 新特性详解》</span>
              <span className="ml-auto text-xs text-muted-foreground">2小时前</span>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-border p-3">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm">在论坛发表了帖子《FastAPI 性能优化指南》</span>
              <span className="ml-auto text-xs text-muted-foreground">1天前</span>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-border p-3">
              <div className="h-2 w-2 rounded-full bg-primary" />
              <span className="text-sm">收藏了文章《PostgreSQL 向量搜索实战》</span>
              <span className="ml-auto text-xs text-muted-foreground">2天前</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
