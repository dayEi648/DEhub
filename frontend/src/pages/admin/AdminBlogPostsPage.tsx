import { useState } from 'react'
import { Search, Edit, Trash2, Eye, EyeOff, Sparkles } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import Pagination from '@/components/ui/Pagination'
import { cn } from '@/lib/utils'

const MOCK_POSTS = [
  { id: 1, title: 'React 19 新特性详解', slug: 'react-19-features', category: { name: '前端开发' }, status: 'published', view_count: 1205, created_at: '2024-01-15T10:00:00' },
  { id: 2, title: 'FastAPI 性能优化指南', slug: 'fastapi-performance', category: { name: '后端开发' }, status: 'published', view_count: 892, created_at: '2024-01-14T08:30:00' },
  { id: 3, title: 'LangGraph 工作流设计模式', slug: 'langgraph-patterns', category: { name: 'AI' }, status: 'draft', view_count: 0, created_at: '2024-01-13T14:00:00' },
  { id: 4, title: 'PostgreSQL 向量搜索实战', slug: 'pgvector-tutorial', category: { name: '数据库' }, status: 'published', view_count: 743, created_at: '2024-01-12T09:00:00' },
  { id: 5, title: 'Docker 多阶段构建优化', slug: 'docker-multi-stage', category: { name: '运维' }, status: 'draft', view_count: 0, created_at: '2024-01-11T16:00:00' },
]

export default function AdminBlogPostsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-bold">博客文章管理</h1>
          <p className="text-sm text-muted-foreground">管理博客文章的发布、编辑与删除</p>
        </div>
        <Button className="gap-1">
          <Sparkles className="h-4 w-4" />
          AI生成摘要
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="搜索文章标题..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">状态：</span>
              <button
                onClick={() => setFilterStatus(null)}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterStatus === null ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                全部
              </button>
              <button
                onClick={() => setFilterStatus('published')}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterStatus === 'published' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                已发布
              </button>
              <button
                onClick={() => setFilterStatus('draft')}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm transition-colors',
                  filterStatus === 'draft' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:bg-muted/80'
                )}
              >
                草稿
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Posts Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">ID</th>
                  <th className="px-4 py-3 text-left font-medium">标题</th>
                  <th className="px-4 py-3 text-left font-medium">分类</th>
                  <th className="px-4 py-3 text-left font-medium">状态</th>
                  <th className="px-4 py-3 text-left font-medium">浏览量</th>
                  <th className="px-4 py-3 text-left font-medium">创建时间</th>
                  <th className="px-4 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {MOCK_POSTS.map(post => (
                  <tr key={post.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3 text-muted-foreground">{post.id}</td>
                    <td className="px-4 py-3 font-medium max-w-xs truncate">{post.title}</td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary">{post.category.name}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      {post.status === 'published' ? (
                        <Badge variant="outline" className="text-emerald-500 border-emerald-500/20">已发布</Badge>
                      ) : (
                        <Badge variant="outline" className="text-yellow-500 border-yellow-500/20">草稿</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{post.view_count}</td>
                    <td className="px-4 py-3 text-muted-foreground">{new Date(post.created_at).toLocaleDateString('zh-CN')}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {post.status === 'published' ? (
                          <Button variant="ghost" size="icon" className="h-8 w-8" title="下线">
                            <EyeOff className="h-4 w-4" />
                          </Button>
                        ) : (
                          <Button variant="ghost" size="icon" className="h-8 w-8" title="发布">
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-center">
        <Pagination currentPage={currentPage} totalPages={3} onPageChange={setCurrentPage} />
      </div>
    </div>
  )
}
