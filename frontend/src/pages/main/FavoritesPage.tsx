import { useState } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, MessageSquare, Trash2, Clock } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

const MOCK_BLOG_FAVORITES = [
  {
    id: 1,
    title: 'React 19 新特性详解：从 use 到 Server Components',
    slug: 'react-19-features',
    category: { name: '前端开发' },
    created_at: '2024-01-15T10:00:00',
  },
  {
    id: 2,
    title: 'FastAPI 性能优化指南：从入门到生产',
    slug: 'fastapi-performance',
    category: { name: '后端开发' },
    created_at: '2024-01-14T08:30:00',
  },
]

const MOCK_FORUM_FAVORITES = [
  {
    id: 1,
    title: 'React 19 的 use() Hook 有什么实际使用场景？',
    zone_name: '前端开发',
    created_at: '2024-01-15T10:00:00',
  },
]

export default function FavoritesPage() {
  const [activeTab, setActiveTab] = useState('blog')

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold mb-6">我的收藏</h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="blog">
            <BookOpen className="h-4 w-4 mr-1" />
            博客文章 ({MOCK_BLOG_FAVORITES.length})
          </TabsTrigger>
          <TabsTrigger value="forum">
            <MessageSquare className="h-4 w-4 mr-1" />
            论坛帖子 ({MOCK_FORUM_FAVORITES.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="blog">
          <div className="space-y-3">
            {MOCK_BLOG_FAVORITES.map(post => (
              <Card key={post.id} className="transition-colors hover:bg-muted/50">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="secondary">{post.category.name}</Badge>
                      </div>
                      <Link to={`/blog/${post.slug}`} className="font-semibold hover:text-primary transition-colors">
                        {post.title}
                      </Link>
                      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        收藏于 {new Date(post.created_at).toLocaleDateString('zh-CN')}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive shrink-0">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="forum">
          <div className="space-y-3">
            {MOCK_FORUM_FAVORITES.map(post => (
              <Card key={post.id} className="transition-colors hover:bg-muted/50">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="secondary">{post.zone_name}</Badge>
                      </div>
                      <Link to={`/forum/post/${post.id}`} className="font-semibold hover:text-primary transition-colors">
                        {post.title}
                      </Link>
                      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        收藏于 {new Date(post.created_at).toLocaleDateString('zh-CN')}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" className="text-destructive hover:text-destructive shrink-0">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
